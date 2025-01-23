import pytest
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
def test_trim_video_functional():
    client = APIClient()
    setup_user(client)

    # Create a test video record
    video = Video.objects.create(
        name="test_video1.mp4",
        duration=30,
        size=1024,
        file="videos/tests/assets/test_video1.mp4"
    )
    print(f"Created video: {video.id}")

    # Make the trim request
    response = client.post(
        f"/api/videos/{video.id}/trim/",
        {"start_time": 5, "end_time": 10},
        format="json"
    )
    print(f"Response Data: {response.data}")

    # Assert the API response
    assert response.status_code == 202, f"Unexpected response: {response.data}"
    assert "task_id" in response.data

    # Verify that the task ID is returned
    task_id = response.data["task_id"]
    print(f"Task ID: {task_id}")
