from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST # Import require_POST
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.utils import timezone

from videos.imagekit_client import upload_avatar
from videos.models import Video, VideoLike, Comment


from .forms import CustomUserCreationForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile, Subscription # Ensure Subscription is imported


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")




def edit_profile(request):
    if request.method == 'POST':

        # ... ادامه کدهای فرم ...
        if 'avatar' in request.FILES:
            file_obj = request.FILES['avatar']
            # آپلود در ImageKit
            upload_info = imagekit.upload_avatar(
                file=file_obj,
                file_name=f"avatar_{request.user.id}.jpg"
            )
            # ذخیره آدرس در دیتابیس
            request.user.profile.avatar_url = upload_info.response_metadata.url
            request.user.profile.save()

        # ادامه عملیات...


@login_required
def profile(request):
    profile_obj, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile_obj)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            profile_instance = p_form.save(commit=False)

            if 'avatar' in request.FILES:
                try:
                    file_obj = request.FILES['avatar']
                    upload_info = upload_avatar(
                        file_data=file_obj.read(),
                        file_name=f"avatar_{request.user.id}.jpg"
                    )

                    profile_instance.avatar_url = upload_info["url"]

                except Exception as e:
                    messages.error(request, f"Error in uploading Avatar: {str(e)}")
            profile_instance.save()
            messages.success(request, "Profile Is Updated Successfully")
            return redirect("accounts:profile")
        else:
            messages.error(request, "Correct The Errors.")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile_obj)

    return render(request, "accounts/profile.html", {
        "u_form": u_form,
        "p_form": p_form,
        "profile_obj": profile_obj,
    })

@login_required
@require_POST
def toggle_subscribe(request, username):
    channel_user = get_object_or_404(User, username=username)

    if request.user == channel_user:
        return JsonResponse({
            "success": False,
            "error": "You Can Not Subscribe Your Own Channel."
        }, status=400)
    sub, created = Subscription.objects.get_or_create(
        subscriber=request.user,
        channel=channel_user
    )
    if created:
        subscribed = True
    else:
        sub.delete()
        subscribed = False
    sub_count = Subscription.objects.filter(channel=channel_user).count()

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
        .select_related('video', 'video__user', 'video__user__profile')
        .order_by('-created_at')
    )

    likes = (
        VideoLike.objects
        .filter(user=request.user)
        .select_related('video', 'video__user', 'video__user__profile')
        .order_by('-created_at')
    )

    events = []

    for c in comments:
        events.append({
            "type": "comment",
            "created_at": c.created_at,
            "video": c.video,
            "text": c.text,
        })

    for l in likes:
        events.append({
            "type": "like" if l.value == VideoLike.LIKE else "dislike",
            "created_at": l.created_at,
            "video": l.video,
            "value": l.value,
        })

    events.sort(key=lambda e: e["created_at"], reverse=True)

    return render(request, "accounts/history.html", {
        "events": events,
    })





@login_required
def subscriptions(request):
    subs = (
        Subscription.objects
        .filter(subscriber=request.user)
        .select_related('channel', 'channel__profile')
        .order_by('-created_at')
    )

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


User = get_user_model()

def public_profile(request, username):
    user_obj = get_object_or_404(User, username=username)
    return render(request, 'accounts/public_profile.html',{
        'profile_user': user_obj

    })