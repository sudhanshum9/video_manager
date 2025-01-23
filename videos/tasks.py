from celery import shared_task
import moviepy.editor as mp
import os
from django.core.files.base import ContentFile
import PIL.Image

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

@shared_task
def trim_video_task(file_path, start_time, end_time, output_path):
    """
    Task to trim a video asynchronously.
    """
    try:
        if not os.path.exists(file_path):
            return {'status': 'error', 'error': 'File not found.'}

        video = mp.VideoFileClip(file_path)

        if start_time < 0 or end_time > video.duration or start_time >= end_time:
            return {'status': 'error', 'error': 'Invalid start or end time.'}

        trimmed_video = video.subclip(start_time, end_time)
        trimmed_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        duration = trimmed_video.duration
        size = os.path.getsize(output_path)

        video.close()
        trimmed_video.close()

        return {'status': 'success', 'output_path': output_path, 'duration': duration, 'size': size}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


@shared_task
def merge_videos_task(file_paths, output_path):
    """
    Task to merge multiple videos asynchronously, ensuring proper alignment of properties.
    """
    try:
        clips = []
        for path in file_paths:
            clip = mp.VideoFileClip(path)

            # Normalize resolution and frame rate
            clip = clip.resize(height=720)  # Resize to 720p
            clip = clip.set_fps(30)         # Set consistent FPS
            clips.append(clip)

        # Merge clips
        final_clip = mp.concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

        # Gather metadata
        duration = final_clip.duration
        size = os.path.getsize(output_path)

        # Cleanup resources
        for clip in clips:
            clip.close()
        final_clip.close()

        return {'status': 'success', 'output_path': output_path, 'duration': duration, 'size': size}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}




# @shared_task
# def merge_videos_task(file_paths, output_path):
#     """
#     Task to merge multiple videos asynchronously, ensuring proper alignment of properties.
#     """
#     try:
#         clips = []
#         for path in file_paths:
#             clip = mp.VideoFileClip(path)

#             # Normalize resolution and frame rate
#             clip = clip.resize(height=720)  # Resize to 720p
#             clip = clip.set_fps(30)         # Set consistent FPS
#             clips.append(clip)

#         # Merge clips
#         final_clip = mp.concatenate_videoclips(clips, method="compose")
#         final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

#         # Gather metadata
#         duration = final_clip.duration
#         size = os.path.getsize(output_path)

#         # Cleanup resources
#         for clip in clips:
#             clip.close()
#         final_clip.close()

#         return {'status': 'success', 'output_path': output_path, 'duration': duration, 'size': size}
#     except Exception as e:
#         return {'status': 'error', 'error': str(e)}


# @shared_task
# def merge_videos_task(file_paths, output_path):
#     """
#     Task to merge multiple videos asynchronously.
#     """
#     try:
#         if not all([os.path.exists(path) for path in file_paths]):
#             return {'status': 'error', 'error': 'One or more files not found.'}

#         clips = [mp.VideoFileClip(path) for path in file_paths]
#         final_clip = mp.concatenate_videoclips(clips)
#         # final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
#         final_clip.write_videofile(output_path)

#         merged_content = ContentFile(open(output_path, "rb").read(), name=output_path)
#         duration = final_clip.duration
#         size = os.path.getsize(output_path)

#         for clip in clips:
#             clip.close()
#         final_clip.close()

#         return {'status': 'success', 'output_path': output_path, 'duration': duration, 'size': size}
#     except Exception as e:
#         return {'status': 'error', 'error': str(e)}
