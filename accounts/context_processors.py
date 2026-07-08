from .models import Notification

def unread_notifications(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
    else:
        count = 0

    return {
        "unread_notifications": count
    }