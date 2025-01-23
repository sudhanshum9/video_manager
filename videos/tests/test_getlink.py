import pytest
import os
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.core.signing import TimestampSigner
from django.utils.timezone import now
from videos.models import Video
from django.conf import settings


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

    # Create a test video
    video = Video.objects.create(
        name="2260991-uhd_3840_2160_24fps.mp4",
        duration=10,
        size=31404195,
        file="videos/uploads/2260991-uhd_3840_2160_24fps.mp4"
    )

    # Make the request to generate an expirable link
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

    # Create a test video
    video = Video.objects.create(
        name="2260991-uhd_3840_2160_24fps.mp4",
        duration=10,
        size=31404195,
        file="videos/uploads/2260991-uhd_3840_2160_24fps.mp4"
    )

    full_path = os.path.join(settings.MEDIA_ROOT, video.file.path)
    assert os.path.exists(full_path), f"Test video file does not exist at {full_path}"

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