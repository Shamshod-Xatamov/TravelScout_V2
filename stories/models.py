import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils.timesince import timesince

# 1. MUHIM IMPORT (Buni qo'shdik)
from cloudinary_storage.storage import MediaCloudinaryStorage


class Story(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    share_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Layk va Saqlanganlar
    likes = models.ManyToManyField(User, related_name='liked_stories', blank=True)
    saved_by = models.ManyToManyField(User, related_name='saved_stories', blank=True)

    # Ko'rishlar soni
    views_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_date(self):
        return timesince(self.created_at) + " ago"


# Rasm (Bitta hikoyada ko'p rasm bo'lishi mumkin)
class StoryImage(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='images')

    # 2. O'ZGARGAN JOY: storage=MediaCloudinaryStorage() qo'shildi
    # Endi bu rasm ham to'g'ri Cloudinaryga yuklanadi
    image = models.ImageField(
        upload_to='story_images/',
        storage=MediaCloudinaryStorage()
    )


# Kommentlar
class Comment(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def get_date(self):
        return timesince(self.created_at) + " ago"