# Video Upload and Processing API

This project provides a Django-based backend application for managing video uploads, chunked uploads, trimming, merging, and generating expirable links for videos. Using **Celery** and **Redis** for asynchronous task execution.

---

## Features

- **Normal Video Upload**: Upload video files directly.
- **Chunked Video Upload**: Handle large file uploads by splitting them into smaller chunks.
- **Video Trimming**: Trim a video file based on start and end times.
- **Video Merging**: Merge multiple video files into one.
- **Expirable Links**: Generate expirable download links for videos.
- **Asynchronous Processing**: All time-consuming tasks (e.g., trimming, merging) are handled asynchronously using Celery and Redis.
- **Authentication**: All endpoints are protected and require an authentication token.

---

## Prerequisites

Ensure you have the following installed on your system:

- Python 3.9 or above
- Django 4.x
- Redis
- Celery
- moviepy==1.0
- Virtualenv

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/video-manager.git
   cd video-manager
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv env
   source env/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   Create a `.env` file in the project root and add the following:
   ```
   SECRET_KEY=your-django-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   BROKER_URL=redis://localhost:6379/0
   RESULT_BACKEND=redis://localhost:6379/0
   ```

5. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the Development Server**:
   ```bash
   python manage.py runserver
   ```

8. **Start Redis and Celery**:
   - Start Redis:
     ```bash
     redis-server
     ```
   - Start Celery Worker:
     ```bash
     celery -A video_manager worker --loglevel=info
     ```

---

## Endpoints

### Authentication
- **Login to Obtain Token**:
  ```
  POST /api-token-auth/
  ```

### Video Uploads
- **Normal Video Upload**:
  ```
  POST /api/videos/upload/
  ```
  Request:
  ```json
  {
    "file": "path_to_video_file"
  }
  ```

- **Chunked Video Upload**:
  ```
  POST /api/videos/chunked_upload/
  ```
  Request:
  ```json
  {
    "chunk_number": 1,
    "total_chunks": 4,
    "file_id": "unique_file_id",
    "file_name": "video.mp4",
    "chunk": "binary_chunk_data"
  }
  ```

### Video Processing
- **Trim Video**:
  ```
  POST /api/videos/<uuid:video_id>/trim/
  ```
  Request:
  ```json
  {
    "start_time": 5,
    "end_time": 10
  }
  ```

- **Merge Videos**:
  ```
  POST /api/videos/merge/
  ```
  Request:
  ```json
  {
    "video_ids": ["uuid1", "uuid2"]
  }
  ```

### Expirable Links
- **Generate Expirable Link**:
  ```
  POST /api/videos/<uuid:video_id>/share/
  ```
  Request:
  ```json
  {
    "expiry_time": 60  # Expiry time in seconds
  }
  ```

### Task Status
- **Check Task Status**:
  ```
  GET /api/videos/tasks/<task_id>/status/
  ```

---

## Testing

Run unit and functional tests using `pytest`:

1. **Run Test Coverage**:
   ```bash
   pytest --cov=videos --cov-report=term --cov-report=html videos/tests/
   ```

1. **Run All Tests**:
   ```bash
   pytest -s --cov=videos videos/tests/
   ```

2. **Run Specific Test**:
   ```bash
   pytest -s videos/tests/test_merge.py
   ```

---

## Key Components

1. **Django Models**:
   - `Video`: Stores metadata for uploaded videos.

2. **Views**:
   - Handles requests for upload, processing, and link generation.

3. **Celery Tasks**:
   - Asynchronous tasks for trimming, merging, and other heavy operations.

4. **Video Processing Utilities**:
   - `moviepy`: Used for video manipulation (e.g., trimming, merging).

---

## Debugging

- **Redis Errors**: Ensure Redis is running:
  ```bash
  redis-server
  ```

- **Task Issues**: Check Celery worker logs for detailed information:
  ```bash
  celery -A video_manager worker --loglevel=info
  ```

---