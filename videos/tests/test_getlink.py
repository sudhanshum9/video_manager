import pytest
import os
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.core.signing import TimestampSigner
from django.utils.timezone import now
from videos.models import Video
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

def setup_user(client):
    """Setup a test user and authenticate the client."""
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="testuser", password="testpass")
    token = Token.objects.create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    print(f"Token: {token.key}")
    return user


@pytest.mark.django_db
def test_generate_expirable_link():
    client = APIClient()
    setup_user(client)

    test_video_path = os.path.join("videos/tests/assets", "test_video1.mp4")
    assert os.path.exists(test_video_path), f"Test video file does not exist at {test_video_path}"
    with open(test_video_path, "rb") as video_file:
        video = SimpleUploadedFile(
            "test_video1.mp4", video_file.read(), content_type="video/mp4"
        )

        response = client.post("/api/videos/upload/", {"file": video, 'max_size': "31404195"})
    # Make the request to generate an expirable link
    video = Video.objects.last()
    response = client.post(
        f"/api/videos/{video.id}/share/",
        {"expiry_time": 60}
    )

    # Assertions
    assert response.status_code == 200
    assert "link" in response.data
    assert "token" in response.data["link"]
    print(f"Response: {response.data}")


@pytest.mark.django_db
def test_serve_video_with_valid_token():
    client = APIClient()
    setup_user(client)

    test_video_path = os.path.join("videos/tests/assets", "test_video1.mp4")
    assert os.path.exists(test_video_path), f"Test video file does not exist at {test_video_path}"
    with open(test_video_path, "rb") as video_file:
        video = SimpleUploadedFile(
            "test_video1.mp4", video_file.read(), content_type="video/mp4"
        )

        response = client.post("/api/videos/upload/", {"file": video, 'max_size': "31404195"})
    # Make the request to generate an expirable link
    video = Video.objects.last()
    signer = TimestampSigner()
    token = signer.sign_object(
        {
            "video_id": str(video.id),
            "expires_at": now().timestamp() + 60,  # Valid for 1 minute
        }
    )
    print(signer.sign_object(
        {
            "video_id": str(video.id),
            "expires_at": now().timestamp() + 60,  # Valid for 1 minute
        }
    ))
    print('token-->', token)
    # Make the GET request to serve the video
    response = client.get(f"/api/videos/serve/?token={token}")

    # Assertions
    assert response.status_code == 200
    assert response["Content-Type"].startswith("video/")
    assert response.has_header("Content-Disposition")
    print(f"Response headers: {response}")