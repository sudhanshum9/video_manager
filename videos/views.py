import os
import uuid
from datetime import datetime
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Video
from .serializers import VideoSerializer
from .utils import validate_video, generate_expirable_link
from .tasks import trim_video_task, merge_videos_task
from django.http import FileResponse, Http404
from django.core.signing import BadSignature, SignatureExpired
from django.core.signing import TimestampSigner
from django.utils.timezone import now


signer = TimestampSigner()
# Directory for storing temporary chunks
CHUNKS_DIR = os.path.join(settings.MEDIA_ROOT, 'video_chunks')
os.makedirs(CHUNKS_DIR, exist_ok=True)

class VideoGetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        videos = Video.objects.all()
        serializer = VideoSerializer(videos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class VideoUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        max_size = request.data.get("max_size", 5 * 1024 * 1024)
        min_duration = request.data.get("min_duration", 5)
        max_duration = request.data.get("max_duration", 25)

        validation_result = validate_video(file, max_size, min_duration, max_duration)
        if not validation_result["success"]:
            return Response(validation_result["error"], status=status.HTTP_400_BAD_REQUEST)

        video = Video.objects.create(
            file=file,
            name=file.name,
            duration=validation_result["duration"],
            size=file.size,
        )
        return Response(VideoSerializer(video).data, status=status.HTTP_201_CREATED)

class VideoChunkedUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Endpoint to handle chunked file uploads
        """
        try:
            # Extract request data
            chunk_number = int(request.data.get('chunk_number'))
            total_chunks = int(request.data.get('total_chunks'))
            file_id = request.data.get('file_id', str(uuid.uuid4()))
            file_name = request.data.get('file_name')
            chunk = request.FILES['chunk']

            file_dir = os.path.join(CHUNKS_DIR, file_id)
            os.makedirs(file_dir, exist_ok=True)

            # Save the chunk to the session directory
            chunk_path = os.path.join(file_dir, f'chunk_{chunk_number}')
            with open(chunk_path, 'wb') as f:
                for chunk_data in chunk.chunks():
                    f.write(chunk_data)

            # Check if all chunks are uploaded
            if chunk_number == total_chunks:
                final_file_path = os.path.join(settings.MEDIA_ROOT, file_name)
                with open(final_file_path, 'wb') as final_file:
                    for i in range(1, total_chunks + 1):
                        chunk_file_path = os.path.join(file_dir, f'chunk_{i}')
                        with open(chunk_file_path, 'rb') as chunk_file:
                            final_file.write(chunk_file.read())

                # Create a Video object after reassembly
                video_size = os.path.getsize(final_file_path) 
                video = Video.objects.create(
                    file=f"videos/uploads/{file_name}",
                    name=file_name,
                    duration=0,
                    size=video_size,
                )

                # Clean up chunk files and directory
                for i in range(1, total_chunks + 1):
                    os.remove(os.path.join(file_dir, f'chunk_{i}'))
                os.rmdir(file_dir)

                return Response({
                    'message': 'File uploaded successfully!',
                    'video': VideoSerializer(video).data,
                }, status=status.HTTP_201_CREATED)

            return Response({'message': 'Chunk uploaded successfully!'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VideoTrimView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, video_id):
        start_time = int(request.data.get("start_time", 0))
        end_time = int(request.data.get("end_time", 0))
        
        try:
            video = Video.objects.get(id=video_id)
            trimmed_video = f'trimmed_{video.name}_{start_time}_to_{end_time}.mp4'
            output_path = os.path.join(settings.MEDIA_ROOT, trimmed_video)

            # Enqueue Celery task
            task = trim_video_task.delay(video.file.path, start_time, end_time, output_path)
            
            return Response({
                "task_id": task.id,
                "message": "Trimming started."
            }, status=status.HTTP_202_ACCEPTED)
        except Video.DoesNotExist:
            return Response({"error": "Video not found."}, status=status.HTTP_404_NOT_FOUND)


class VideoMergeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        video_ids = request.data.get("video_ids", [])
        print(f'video_ids: {video_ids}')
        try:
            videos = Video.objects.filter(id__in=video_ids)
            file_paths = [video.file.path for video in videos]
            base_names = [os.path.splitext(os.path.basename(video.file.name))[0] for video in videos]
            merged_name = "_".join(base_names)[:50]
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            merged_file_name = f"merged_{merged_name}_{timestamp}.mp4"
            output_path = os.path.join(settings.MEDIA_ROOT, merged_file_name)
            
            # Enqueue Celery task
            task = merge_videos_task.delay(file_paths, output_path)
            print(task)
            return Response({
                "task_id": task.id,
                "message": "Merging started."
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GenerateExpirableLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, video_id):
        expiry_time = request.data.get("expiry_time", 60)  # 1 hour default
        
        try:
            video = Video.objects.get(id=video_id)
            link = generate_expirable_link(video.id, expiry_time)

            return Response({"link": link}, status=status.HTTP_200_OK)
        except Video.DoesNotExist:
            return Response({"error": "Video not found."}, status=status.HTTP_404_NOT_FOUND)
        

class ServeVideoView(APIView):
    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
        if not token:
            raise Http404("Token is missing from the request")

        try:
            
            data = signer.unsign_object(token, max_age=3600)  # Token expires after 1 hour
            video_id = data.get('video_id')
            expires_at = data.get('expires_at')

            # Validate expiration
            if expires_at < now().timestamp():
                raise Http404("Token has expired")

            video = Video.objects.get(id=video_id)

            # Serve the video file
            return FileResponse(video.file, as_attachment=False)

        except (BadSignature, SignatureExpired):
            raise Http404("Invalid or expired token")
        except Video.DoesNotExist:
            raise Http404("Video not found")
        except Exception as e:
            raise Http404(f"An error occurred: {str(e)}")