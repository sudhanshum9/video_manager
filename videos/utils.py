from moviepy.editor import VideoFileClip
from django.conf import settings
from django.core.signing import TimestampSigner
from django.utils.timezone import now

signer = TimestampSigner()

def validate_video(file, max_size, min_duration, max_duration):
    if int(file.size) > int(max_size):
        return {"success": False, "error": "File exceeds maximum size."}

    video = VideoFileClip(file.temporary_file_path())
    duration = video.duration

    if duration < min_duration or duration > max_duration:
        return {"success": False, "error": "Video duration out of bounds."}

    return {"success": True, "duration": duration}



def generate_expirable_link(video_id, expire_in_seconds):
    """
    Generate an expiring link for a video.
    """
    # Sign the video ID with expiration
    expire_in_seconds = int(expire_in_seconds)
    token = signer.sign_object({'video_id': str(video_id), 'expires_at': now().timestamp() + expire_in_seconds})
    return f"{settings.SITE_URL}/api/videos/serve/?token={token}"
