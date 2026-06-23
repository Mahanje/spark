from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Create your models here.

class Report(models.Model):
    # دلایل آماده برای گزارش دادن
    REASONS = (
        ('spam', 'Spam'),
        ('abusive', 'Violence Or Abusive'),
        ('copyright', 'Copyright'),
        ('inappropriate', 'Sexual Content Or Inappropriate'),
        ('other', 'Other'),
    )
    # کسی که گزارش داده (کاربر سایت)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')

    # این سه تا با هم سیستم Generic Relation می‌سازن
    # یعنی گزارش می‌تونه روی هر مدل (Video, Comment, ...) اعمال بشه
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # دلیل گزارش (از REASONS انتخاب میشه)
    reason = models.CharField(max_length=20, choices=REASONS)
    description = models.TextField(blank=True, null=True, verbose_name="Additional Information")

    created_at = models.DateTimeField(auto_now_add=True)
    # وضعیت بررسی شدن گزارش توسط ادمین
    is_resolved = models.BooleanField(default=False, verbose_name="Checked")

    def __str__(self):
        return f"Report  {self.user} On {self.content_object}"