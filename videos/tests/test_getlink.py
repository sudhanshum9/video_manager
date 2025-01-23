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
def test_generate_expirable_link():
    client = APIClient()
    setup_user(client)

    # Create a test video record
    video = Video.objects.create(
        name="test.mp4",
        duration=30,
        size=1024,
        file="videos/uploads/test.mp4"
    )
    print(f"Created video: {video.id}")

    # Make the request to generate an expirable link
    response = client.post(
        f"/api/videos/{video.id}/share/",
        {"expiry_time": 60}
    )
    print(f"Response Data: {response.data}")  # Debugging response data

    # Assertions
    assert response.status_code == 200, f"Unexpected response: {response.data}"
    assert "link" in response.data
    assert response.data["link"].startswith("http")  # Ensure the link looks valid