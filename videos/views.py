
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Video
from .serializers import VideoSerializer
from .utils import validate_video, trim_video, merge_videos, generate_expirable_link


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

class VideoTrimView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, video_id):
        start_time = int(request.data.get("start_time", 0))
        end_time = int(request.data.get("end_time", 0))
        
        try:
            video = Video.objects.get(id=video_id)
            trimmed_video = trim_video(video.file.path, start_time, end_time)
            video.file.save(trimmed_video.name, trimmed_video)
            return Response(VideoSerializer(video).data, status=status.HTTP_200_OK)
        except Video.DoesNotExist:
            return Response({"error": "Video not found."}, status=status.HTTP_404_NOT_FOUND)


class VideoMergeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        video_ids = request.data.get("video_ids", [])
        
        try:
            videos = Video.objects.filter(id__in=video_ids)
            if len(videos) < len(video_ids):
                return Response({"error": "Some videos were not found."}, status=status.HTTP_404_NOT_FOUND)

            merged_video_content, duration, size = merge_videos([video.file.path for video in videos])
            new_video = Video.objects.create(
                file=merged_video_content,
                name="merged_video.mp4",
                duration=duration,
                size=size,
            )
            return Response(VideoSerializer(new_video).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

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
