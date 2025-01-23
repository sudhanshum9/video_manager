
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.conf import settings

def validate_video(file, max_size, min_duration, max_duration):
    if int(file.size) > int(max_size):
        return {"success": False, "error": "File exceeds maximum size."}

    video = VideoFileClip(file.temporary_file_path())
    duration = video.duration

    if duration < min_duration or duration > max_duration:
        return {"success": False, "error": "Video duration out of bounds."}

    return {"success": True, "duration": duration}


def trim_video(file_path, start_time, end_time):
    """
    Trims the video file at the given path from `start_time` to `end_time`.

    :param file_path: Path to the video file.
    :param start_time: Start time in seconds.
    :param end_time: End time in seconds.
    :return: ContentFile containing the trimmed video.
    :raises: ValueError if times are invalid or processing fails.
    """
    try:
        video = VideoFileClip(file_path)

        # Validate times
        if start_time < 0 or end_time > video.duration or start_time >= end_time:
            raise ValueError("Invalid start or end time.")

        # Trim video
        trimmed_video = video.subclip(start_time, end_time)
        trimmed_path = f"trimmed_{get_random_string(8)}.mp4"

        # Write trimmed video
        trimmed_video.write_videofile(trimmed_path, codec="libx264", audio_codec="aac")

        # Return the trimmed video as ContentFile
        return ContentFile(open(trimmed_path, "rb").read(), name=trimmed_path)

    except Exception as e:
        raise ValueError(f"Error while trimming video: {e}")




def merge_videos(file_paths):
    print(f'file_paths: {file_paths}')
    clips = [VideoFileClip(path) for path in file_paths]
    final_clip = concatenate_videoclips(clips)
    merged_path = f"merged_{get_random_string(8)}.mp4"
    final_clip.write_videofile(merged_path)

    merged_content = ContentFile(open(merged_path, "rb").read(), name=merged_path)
    duration = final_clip.duration
    size = os.path.getsize(merged_path)
    return merged_content, duration, size


def generate_expirable_link(file_url, expiry_time):
    return f"{settings.BASE_URL}{file_url}?expiry={expiry_time}"