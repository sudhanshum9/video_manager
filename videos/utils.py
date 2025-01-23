from moviepy.editor import VideoFileClip
from django.conf import settings

def validate_video(file, max_size, min_duration, max_duration):
    if int(file.size) > int(max_size):
        return {"success": False, "error": "File exceeds maximum size."}

    video = VideoFileClip(file.temporary_file_path())
    duration = video.duration

    if duration < min_duration or duration > max_duration:
        return {"success": False, "error": "Video duration out of bounds."}

    return {"success": True, "duration": duration}


def generate_expirable_link(file_url, expiry_time):
    return f"{settings.BASE_URL}{file_url}?expiry={expiry_time}"