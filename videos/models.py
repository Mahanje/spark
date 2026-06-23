from django.db import models
from django.contrib.auth.models import User

# from .imagekit_client import (
#     get_optimized_video_url, get_streaming_url, get_thumbnail_url, add_image_watermark
# )


# این کلاس ینی یک جدول در دیتابیس به اسم Video
class Video(models.Model):
    # هر ویدیو مال یک کاربره , اگر کاربر حذف بشه همه ویدیوهاش هم حذف میشن
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="videos")
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    file_id = models.CharField(max_length=200)
    video_url = models.URLField(max_length=500)
    thumbnail_url = models.URLField(max_length=500, blank=True)

    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ترتیب نمایش ویدیوها به ترتیب از قدیم به جدید
    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    # این قسمت‌ها property هستن یعنی فیلد دیتابیس نیستن، بلکه محاسبه‌ای (computed) هستن و هر بار که صداشون بزنی، مقدار رو لحظه‌ای می‌سازن.
    @property
    def display_thumbnail_url(self):
        if self.thumbnail_url:
            return self.thumbnail_url  # همون چیزی که کاربر گذاشته

        return "/static/images/images (1).png"

    # @property
    # def generated_thumbnail_url(self):
    #     if not self.video_url:
    #         return ""
    #     return get_thumbnail_url(self.video_url, self.user.username)

    # @property
    # def streaming_url(self):
    #     if not self.video_url:
    #         return ""
    #     return get_streaming_url(self.video_url)
    #
    # @property
    # def optimized_url(self):
    #     if not self.video_url:
    #         return ""
    #     return get_optimized_video_url(self.video_url)


class Comment(models.Model):
    # هر کامنت مربوط به یک ویدیو است اگر ویدیو حذف شود همه کامنت‌ها هم حذف می‌شوند
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.video.title}"


class VideoLike(models.Model):
    LIKE = 1
    DISLIKE = -1
    LIKE_CHOICES = [
        (LIKE, "Like"),
        (DISLIKE, "Dislike")
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="user_likes")
    value = models.SmallIntegerField(choices=LIKE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    # جلوگیری از رای تکراری
    class Meta:
        unique_together = ["user", "video"]

    def __str__(self):
        action = "liked" if self.value == self.LIKE else "disliked"
        return f"{self.user.username} {action} {self.video.title}"

