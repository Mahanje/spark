from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings  # Import settings


class Profile(models.Model):
    # ارتباط یک به یک با User هر کاربر فقط یک پروفایل دارد با حذف User پروفایل هم حذف می‌شود
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # آدرس عکس پروفایل ذخیره‌شده در ImageKit  می‌تواند خالی باشد
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    # شناسه فایل در ImageKit  برای حذف فایل از ImageKit کاربرد دارد
    avatar_file_id = models.CharField(max_length=100, blank=True, null=True)

    # نمایش خواناتر آبجکت در پنل ادمین و Shell
    def __str__(self):
        return f"Profile of {self.user.username}"


# این جدول در دیتابیس یک رابطه Follower / Following می‌سازد
class Subscription(models.Model):
    # subscriber
    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use settings.AUTH_USER_MODEL for ForeignKey
        on_delete=models.CASCADE,
        related_name='following'
    )
    # subscribed channel
    channel = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use settings.AUTH_USER_MODEL for ForeignKey
        on_delete=models.CASCADE,
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # این خط باعث می‌شود یک کاربر نتواند یک کانال را دوبار سابسکرایب کند
        unique_together = ('subscriber', 'channel')

    def __str__(self):
        return f"{self.subscriber.username} subscribed to {self.channel.username}"


# وقتی یک User ذخیره می‌شود، این signal اجرا می‌شود
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # اگر این User تازه ساخته شده باشد
    if created:
        # برایش یک Profile هم ساخته می‌شود
        Profile.objects.create(user=instance)

# هر بار که User ذخیره شود (حتی edit)، این signal اجرا می‌شود
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # پروفایل مرتبط هم ذخیره می‌شود
    instance.profile.save()
