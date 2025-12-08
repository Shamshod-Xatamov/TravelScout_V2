from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import uuid



class Trip(models.Model):
    BUDGET_CHOICES = [
        ('Economy', 'Economy'),
        ('Standard', 'Standard'),
        ('Luxury', 'Luxury'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.CharField(max_length=200)
    start_date = models.DateField(default=timezone.now)
    duration_days = models.IntegerField(default=5)

    budget_type = models.CharField(max_length=20, choices=BUDGET_CHOICES, default='Standard')
    budget_amount = models.IntegerField(default=1200)
    share_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    description = models.TextField(blank=True, default="A personalized AI travel plan.")
    interests = models.CharField(max_length=500, default="Culture, Food")

    cover_image = models.ImageField(upload_to='trip_covers/', blank=True, null=True)
    is_favorite = models.BooleanField(default=False)

    # --- O'ZGARISH SHU YERDA ---
    # Oldin: generated_plan = ...
    # Hozir: itinerary = ... (View bilan bir xil bo'lishi shart)
    itinerary = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def get_interests_list(self):
        return [x.strip() for x in self.interests.split(',')]

    def __str__(self):
        return f"{self.destination} ({self.user.username})"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Rasm yuklanadigan joy
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"

# --- SIGNAL: User yaratilganda avtomatik Profile ham yaratilsin ---
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()