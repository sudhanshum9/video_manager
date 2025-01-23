from django.urls import path
from .views import VideoUploadView, VideoTrimView, VideoGetView, VideoMergeView, GenerateExpirableLinkView, VideoChunkedUploadView, TaskStatusView

urlpatterns = [
    path("list/", VideoGetView.as_view(), name="get-videos"),
    path("upload/", VideoUploadView.as_view(), name="video-upload"),
    path('chunked_upload/', VideoChunkedUploadView.as_view(), name='chunked_upload'),
    path("<uuid:video_id>/trim/", VideoTrimView.as_view(), name="video-trim"),
    path("merge/", VideoMergeView.as_view(), name="video-merge"),
    path("<uuid:video_id>/share/", GenerateExpirableLinkView.as_view(), name="video-share"),
    path("tasks/<task_id>/status/", TaskStatusView.as_view(), name="task-status"),
]
