from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings # Import settings

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar_file_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

class Subscription(models.Model):
    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Use settings.AUTH_USER_MODEL for ForeignKey
        on_delete=models.CASCADE,
        related_name='following'
    )
    channel = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Use settings.AUTH_USER_MODEL for ForeignKey
        on_delete=models.CASCADE,
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # این خط باعث می‌شود یک کاربر نتواند یک کانال را دوبار سابسکرایب کند
        unique_together = ('subscriber', 'channel')

    def __str__(self):
        return f"{self.subscriber.username} subscribed to {self.channel.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """هر وقت User جدید ساخته شد، Profile هم ساخته شود."""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """هر وقت User ذخیره شد، Profile هم ذخیره شود."""
    instance.profile.save()