import pytest
from rest_framework.test import APIClient
from videos.models import Video
from rest_framework.authtoken.models import Token


def setup_user(client):
    """Setup a test user and authenticate the client."""
    from django.contrib.auth.models import User
    # Create a user and generate a token
    user = User.objects.create_user(username="testuser", password="testpass")
    token = Token.objects.create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    print(f"Token: {token.key}")

    return user


@pytest.mark.django_db
def test_list_videos():
    client = APIClient()
    setup_user(client)

    # Create test videos
    video1 = Video.objects.create(
        name="video1.mp4",
        duration=10,
        size=500,
        file="videos/uploads/video1.mp4"
    )
    video2 = Video.objects.create(
        name="video2.mp4",
        duration=15,
        size=700,
        file="videos/uploads/video2.mp4"
    )
    print(f"Created videos: {video1}, {video2}")

    # Call the list API
    response = client.get("/api/videos/list/")
    print(response.data)  # Debugging response data

    # Assertions
    assert response.status_code == 200, f"Unexpected response: {response.data}"
    assert len(response.data) == 2
    assert response.data[0]["name"] == "video1.mp4"
    assert response.data[1]["name"] == "video2.mp4"
