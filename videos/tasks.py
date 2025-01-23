from celery import shared_task, current_task
import moviepy.editor as mp
import os
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


@shared_task(bind=True)
def merge_videos_task(self, file_paths, output_path):
    """
    Task to merge multiple videos asynchronously, with status updates.
    """
    try:
        self.update_state(state="STARTED", meta={"message": "Merging videos has started."})
        current_task.update_state(state="STARTED", meta={"message": "Task started"})

        clips = []
        for i, path in enumerate(file_paths):
            clip = mp.VideoFileClip(path)
            clip = clip.resize(height=720)  # Optional: Normalize resolution
            clip = clip.set_fps(30)         # Optional: Normalize FPS
            clips.append(clip)

            # Update task progress
            self.update_state(
                state="PROGRESS",
                meta={
                    "message": f"Processing clip {i+1} of {len(file_paths)}.",
                    "current": i + 1,
                    "total": len(file_paths),
                }
            )

        # Merge the clips
        final_clip = mp.concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

        # Clean up resources
        for clip in clips:
            clip.close()
        final_clip.close()

        # Update task status to SUCCESS
        self.update_state(state="SUCCESS", meta={"output_path": output_path})
        current_task.update_state(state="SUCCESS", meta={"output_path": output_path})

        return {"status": "success", "output_path": output_path}
    except Exception as e:
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise