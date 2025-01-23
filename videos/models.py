
from django.db import models
import os
from uuid import uuid4

class Video(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    file = models.FileField(upload_to="videos/uploads/") # we can change it as per our needs
    name = models.CharField(max_length=255)
    duration = models.PositiveIntegerField()  # seconds
    size = models.PositiveIntegerField()  # bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name