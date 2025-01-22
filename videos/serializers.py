from rest_framework import serializers
from .models import Video

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ["id", "name", "duration", "size", "file", "uploaded_at"]
