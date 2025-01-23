import pytest
import os
from rest_framework.test import APIClient
from videos.models import Video
from rest_framework.authtoken.models import Token


def setup_user(client):
    """Setup a test user and authenticate the client."""
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="testuser", password="testpass")
    token = Token.objects.create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    print(f"Token: {token.key}")
    return user

@pytest.mark.django_db
def test_merge_videos_functional():
    client = APIClient()
    setup_user(client)

    # Create test videos with real file paths
    video1 = Video.objects.create(
        name="test_video1.mp4",
        duration=20,
        size=31404195,
        file="videos/tests/assets/test_video1.mp4"
    )
    video2 = Video.objects.create(
        name="test_video2.mp4",
        duration=10,
        size=55166599,
        file="videos/tests/assets/test_video2.mp4"
    )

    # Prepare payload
    payload = {"video_ids": [str(video1.id), str(video2.id)]}

    # Make the request
    response = client.post(
        "/api/videos/merge/",
        payload,
        format="json"
    )
    print(f"Response Data: {response.data}")

    # Assert the API response
    assert response.status_code == 202, f"Unexpected response: {response.data}"
    assert "task_id" in response.data