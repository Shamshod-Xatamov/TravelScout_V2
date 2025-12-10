import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils.timesince import timesince


class Story(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    share_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # Layk va Saqlanganlar (Many-to-Many - chunki ko'p user ko'p layk bosishi mumkin)
    likes = models.ManyToManyField(User, related_name='liked_stories', blank=True)
    saved_by = models.ManyToManyField(User, related_name='saved_stories', blank=True)

    # Ko'rishlar soni
    views_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']  # Eng yangisi tepada turadi

    def __str__(self):
        return self.title

    # Vaqtni chiroyli ko'rsatish uchun (masalan: "2 hours ago")
    def get_date(self):
        return timesince(self.created_at) + " ago"


# Rasm (Bitta hikoyada ko'p rasm bo'lishi mumkin)
class StoryImage(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='story_images/')


# Kommentlar
class Comment(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def get_date(self):
        return timesince(self.created_at) + " ago"