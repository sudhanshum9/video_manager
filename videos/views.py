import os
import uuid
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Video
from .serializers import VideoSerializer
from .utils import validate_video, trim_video, merge_videos, generate_expirable_link
from .tasks import trim_video_task, merge_videos_task


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
        Endpoint to handle chunked file uploads.
        """
        try:
            chunk_number = int(request.data.get('chunk_number'))
            total_chunks = int(request.data.get('total_chunks'))
            file_id = request.data.get('file_id', str(uuid.uuid4()))
            file_name = request.data.get('file_name')
            chunk = request.FILES['chunk']

            # Create a unique directory for each upload session
            file_dir = os.path.join(CHUNKS_DIR, file_id)
            os.makedirs(file_dir, exist_ok=True)

            # Save the chunk
            chunk_path = os.path.join(file_dir, f'chunk_{chunk_number}')
            with open(chunk_path, 'wb') as f:
                for chunk_data in chunk.chunks():
                    f.write(chunk_data)

            # Check if all chunks are uploaded
            if chunk_number == total_chunks:
                # Reassemble the chunks into the final file
                final_file_path = os.path.join(settings.MEDIA_ROOT, file_name)
                with open(final_file_path, 'wb') as final_file:
                    for i in range(1, total_chunks + 1):
                        chunk_file_path = os.path.join(file_dir, f'chunk_{i}')
                        with open(chunk_file_path, 'rb') as chunk_file:
                            final_file.write(chunk_file.read())

                # Clean up chunk files
                for i in range(1, total_chunks + 1):
                    os.remove(os.path.join(file_dir, f'chunk_{i}'))
                os.rmdir(file_dir)

                return Response({
                    'message': 'File uploaded successfully!',
                    'file_path': final_file_path
                }, status=200)

            return Response({'message': 'Chunk uploaded successfully!'}, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=400)


# class VideoTrimView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, video_id):
#         start_time = int(request.data.get("start_time", 0))
#         end_time = int(request.data.get("end_time", 0))
        
#         try:
#             video = Video.objects.get(id=video_id)
#             trimmed_video = trim_video(video.file.path, start_time, end_time)
#             video.file.save(trimmed_video.name, trimmed_video)
#             return Response(VideoSerializer(video).data, status=status.HTTP_200_OK)
#         except Video.DoesNotExist:
#             return Response({"error": "Video not found."}, status=status.HTTP_404_NOT_FOUND)


class VideoTrimView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, video_id):
        start_time = int(request.data.get("start_time", 0))
        end_time = int(request.data.get("end_time", 0))
        
        try:
            video = Video.objects.get(id=video_id)
            trimmed_video = f'trimmed_{start_time}_to_{end_time}.mp4'
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
        
        try:
            videos = Video.objects.filter(id__in=video_ids)
            # if len(videos) < len(video_ids):
            #     return Response({"error": "Some videos were not found."}, status=status.HTTP_404_NOT_FOUND)
            
            file_paths = [video.file.path for video in videos]
            output_path = os.path.join(settings.MEDIA_ROOT, "merged_video_2.mp4")
            
            # Enqueue Celery task
            task = merge_videos_task.delay(file_paths, output_path)
            
            return Response({
                "task_id": task.id,
                "message": "Merging started."
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TaskStatusView(APIView):
    """
    Endpoint to check the status of a task.
    """
    def get(self, request, task_id):
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        return Response({
            "task_id": task_id,
            "status": result.status,
            "result": result.result
        })


# class VideoMergeView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         video_ids = request.data.get("video_ids", [])
        
#         try:
#             videos = Video.objects.filter(id__in=video_ids)
#             if len(videos) < len(video_ids):
#                 return Response({"error": "Some videos were not found."}, status=status.HTTP_404_NOT_FOUND)

#             merged_video_content, duration, size = merge_videos([video.file.path for video in videos])
#             new_video = Video.objects.create(
#                 file=merged_video_content,
#                 name="merged_video.mp4",
#                 duration=duration,
#                 size=size,
#             )
#             return Response(VideoSerializer(new_video).data, status=status.HTTP_201_CREATED)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class GenerateExpirableLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, video_id):
        expiry_time = request.data.get("expiry_time", 60)  # 1 hour default
        
        try:
            video = Video.objects.get(id=video_id)
            link = generate_expirable_link(video.file.url, expiry_time)
            return Response({"link": link}, status=status.HTTP_200_OK)
        except Video.DoesNotExist:
            return Response({"error": "Video not found."}, status=status.HTTP_404_NOT_FOUND)
