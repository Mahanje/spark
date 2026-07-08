from django.shortcuts import render, redirect, \
    get_object_or_404  # گرفتن یک شیء از دیتابیس؛ اگر پیدا نشود خطای 404 می‌دهد.
from django.contrib import messages  # برای نمایش پیام‌های موفقیت یا خطا
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy  # برای ساخت URL بر اساس نام Route
from django.views.generic import CreateView
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST  # Import require_POST
from django.http import JsonResponse

from videos.imagekit_client import upload_avatar
from videos.models import Video, VideoLike, Comment

from .forms import CustomUserCreationForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile, Subscription, Notification  # Ensure Subscription is imported


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")


# فقط کاربران لاگین‌شده به این View دسترسی دارند
@login_required
def profile(request):  # گرفتن پروفایل کاربر؛ اگر وجود نداشته باشد ساخته می‌شود
    profile_obj, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":  # اگر متد ارسال پست باشد
        # فرم ویرایش اطلاعات User (مثل username و email)
        u_form = UserUpdateForm(request.POST, instance=request.user)

        # فرم ویرایش Profile (مثل bio و avatar)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile_obj)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            # یک آبجکت Profile بساز و مقادیر فرم را داخلش بریز، ولی هنوز در دیتابیس ذخیره نکن
            profile_instance = p_form.save(commit=False)

            if 'avatar' in request.FILES:
                try:
                    file_obj = request.FILES['avatar']

                    # آپلود عکس در ImageKit
                    upload_info = upload_avatar(
                        file_data=file_obj.read(),
                        file_name=f"avatar_{request.user.id}.jpg"
                    )
                    # ذخیره url عکس
                    profile_instance.avatar_url = upload_info["url"]

                except Exception as e:
                    messages.error(request, f"Error in uploading Avatar: {str(e)}")
            profile_instance.save()
            messages.success(request, "Profile Is Updated Successfully")
            return redirect("accounts:profile")
        else:
            messages.error(request, "Correct The Errors.")  # اگر فرم‌ها معتبر نباشند

    else:  # اگر درخواست GET باشد فرم‌ها با اطلاعات فعلی پر می‌شوند
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile_obj)

    # ارسال فرم‌ها و اطلاعات پروفایل به قالب
    return render(request, "accounts/profile.html", {
        "u_form": u_form,
        "p_form": p_form,
        "profile_obj": profile_obj,
    })


@login_required
@require_POST
def toggle_subscribe(request, username):
    # پیدا کردن صاحب کانال بر اساس username
    # اگر پیدا نشود خطای 404 برمی‌گرداند
    channel_user = get_object_or_404(User, username=username)

    # جلوگیری از سابسکرایب کردن کانال خود
    if request.user == channel_user:
        return JsonResponse({
            "success": False,
            "error": "You Can Not Subscribe Your Own Channel."
        }, status=400)

    # اگر قبلاً Subscription وجود داشته باشد همان را برمی‌گرداند
    # اگر وجود نداشته باشد یکی می‌سازد
    sub, created = Subscription.objects.get_or_create(
        subscriber=request.user,
        channel=channel_user
    )

    if created:
        subscribed = True

        Notification.objects.create(
            receiver=channel_user,
            sender=request.user,
            type=Notification.SUBSCRIBE,
        )

    else:
        sub.delete()
        subscribed = False
    sub_count = Subscription.objects.filter(channel=channel_user).count()  # شمارش تعداد سابسکرایبرهای کانال

    # ارسال نتیجه به فرانت‌اند (Ajax/JavaScript)
    return JsonResponse({
        "success": True,
        "subscribed": subscribed,
        "count": sub_count
    })


@login_required
def history(request):
    comments = (
        Comment.objects
        .filter(user=request.user)
        .select_related(
            'video',
            'video__user',
            'video__user__profile'
        )
    )

    likes = (
        VideoLike.objects
        .filter(user=request.user)
        .select_related(
            'video',
            'video__user',
            'video__user__profile'
        )
    )

    subscriptions = (
        Subscription.objects
        .filter(subscriber=request.user)
        .select_related(
            'channel',
            'channel__profile'
        )
    )

    events = []

    # کامنت‌های خود کاربر
    for c in comments:
        if c.video:
            events.append({
                "type": "comment",
                "created_at": c.created_at,
                "video": c.video,
                "text": c.text,
            })

    # لایک و دیسلایک‌های خود کاربر
    for l in likes:
        if l.video:
            events.append({
                "type": "like" if l.value == VideoLike.LIKE else "dislike",
                "created_at": l.created_at,
                "video": l.video,
            })

    for s in subscriptions:
        events.append({
            "type": "subscribe",
            "created_at": s.created_at,
            "channel": s.channel,
        })

    events.sort(
        key=lambda x: x["created_at"],
        reverse=True
    )

    events_by_date = {}

    for event in events:
        day = event["created_at"].date()
        events_by_date.setdefault(day, []).append(event)

    return render(
        request,
        "accounts/history.html",
        {
            "events_by_date": events_by_date
        }
    )


@login_required
def subscriptions(request):
    subs = (
        Subscription.objects
        .filter(subscriber=request.user)
        .select_related('channel', 'channel__profile')
        .order_by('-created_at')
    )

    # یعنی فقط کاربرهای کانال‌ها را از آبجکت‌های Subscription استخراج می‌کند.
    channels = [s.channel for s in subs]

    videos = (
        Video.objects
        .filter(user__in=channels)
        .select_related('user', 'user__profile')
        .order_by('-created_at')
    )

    return render(request, 'accounts/subscriptions.html', {
        'channels': channels,
        'videos': videos,
    })


@login_required
def notifications(request):
    Notification.objects.filter(
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    notifications = (
        Notification.objects
        .filter(receiver=request.user)
        .select_related(
            "sender",
            "sender__profile",
            "video",
            "comment",
        )
    )

    for n in notifications:
        n.subscribed_back = Subscription.objects.filter(
            subscriber=request.user,
            channel=n.sender
        ).exists()

    return render(
        request,
        "accounts/notification.html",
        {
            "notifications": notifications
        }
    )


@login_required
def unread_notifications(request):
    count = Notification.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    return JsonResponse({
        "count": count
    })
