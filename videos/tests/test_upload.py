import pytest
import os
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

@pytest.mark.django_db
def test_video_upload_with_token():
    client = APIClient()

    # Create a user and generate a token
    user = User.objects.create_user(username="testuser", password="testpass")
    token = Token.objects.create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    print(f'token, {token}')

    # Load the test video file
    test_video_path = os.path.join("videos/tests/assets", "test_video1.mp4")
    assert os.path.exists(test_video_path), f"Test video file does not exist at {test_video_path}"
    with open(test_video_path, "rb") as video_file:
        video = SimpleUploadedFile(
            "test_video1.mp4", video_file.read(), content_type="video/mp4"
        )

        response = client.post("/api/videos/upload/", {"file": video, 'max_size': "31404195"})

    assert response.status_code == 201
    assert "id" in response.data
