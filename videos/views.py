from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, F
from django.contrib.auth.models import User

from django.contrib.admin.views.decorators import staff_member_required

# ایمپورت مدل‌ها
from .models import Video, VideoLike, Comment
from accounts.models import Subscription, Profile
from .forms import VideoUploadForm

# ایمپورت توابع ImageKit
from .imagekit_client import (
    upload_video,
    upload_thumbnail,
    delete_video as ik_delete_video
)


# در videos/views.py
def video_detail(request, video_id):
    video = get_object_or_404(Video, pk=video_id)

    # افزایش بازدید به صورت اتمیک و سریع
    Video.objects.filter(pk=video_id).update(views=F('views') + 1)
    video.views += 1  # این خط باعث می‌شود عدد جدید در همین لحظه در صفحه نمایش داده شود

    is_subscribed = False
    if request.user.is_authenticated:
        is_subscribed = Subscription.objects.filter(subscriber=request.user, channel=video.user).exists()

    return render(request, 'videos/detail.html', {
        'video': video,
        'is_subscribed': is_subscribed,
    })


# --- لیست ویدیوها در صفحه اصلی ---
def video_list(request):
    videos = Video.objects.all().order_by('-created_at')

    return render(request, 'videos/list.html', {'videos': videos})


# --- جستجوی ویدیو ---


def search_videos(request):
    query = request.GET.get('q')

    if query:
        # جستجوی هوشمند در عنوان ویدیو و نام کاربری سازنده (کانال)
        videos = Video.objects.filter(
            Q(title__icontains=query) |
            Q(user__username__icontains=query)
        ).distinct().order_by('-created_at')
    else:
        # نمایش همه ویدیوها در حالت عادی
        videos = Video.objects.all().order_by('-created_at')

    return render(request, 'videos/list.html', {'videos': videos, 'query': query})


# --- آپلود ویدیو ---
@login_required
@require_POST
def video_upload(request):
    form = VideoUploadForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            video_file = request.FILES.get('video_file')
            if not video_file:
                return JsonResponse({'error': 'No video file provided'}, status=400)

            video_data = upload_video(file_data=video_file.read(), file_name=video_file.name)

            thumbnail_url = ""
            thumbnail_file = request.FILES.get('thumbnail_file')
            thumbnail_data_from_form = request.POST.get('thumbnail_data')

            if thumbnail_file:
                thumb_res = upload_thumbnail(
                    file_data=thumbnail_file.read(),
                    file_name=thumbnail_file.name
                )
                thumbnail_url = thumb_res["url"]

            elif thumbnail_data_from_form:
                thumb_res = upload_thumbnail(
                    file_data=thumbnail_data_from_form,
                    file_name=f"thumb_{video_file.name}.png"
                )
                thumbnail_url = thumb_res["url"]

            video = Video.objects.create(
                user=request.user,
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                file_id=video_data['file_id'],
                video_url=video_data['url'],
                thumbnail_url=thumbnail_url,
            )
            return JsonResponse({'success': True, 'video_id': video.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid form data'}, status=400)


@login_required
def video_upload_page(request):
    return render(request, 'videos/upload.html', {'form': VideoUploadForm()})


# --- حذف ویدیو ---
@login_required
@require_POST
def delete_video(request, video_id):
    video = get_object_or_404(Video, id=video_id, user=request.user)
    try:
        ik_delete_video(video.file_id)
        video.delete()
        return JsonResponse({'success': True, 'message': 'Video deleted successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --- سیستم لایک و دیسلایک ---
@login_required
@require_POST
def video_vote(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    try:
        vote_value = int(request.POST.get('vote'))
        existing_vote = VideoLike.objects.filter(user=request.user, video=video).first()
        user_vote = None

        if existing_vote:
            if existing_vote.value == vote_value:
                if vote_value == VideoLike.LIKE:
                    video.likes -= 1
                else:
                    video.dislikes -= 1
                existing_vote.delete()
            else:
                if existing_vote.value == VideoLike.LIKE:
                    video.likes -= 1
                    video.dislikes += 1
                else:
                    video.dislikes -= 1
                    video.likes += 1
                existing_vote.value = vote_value
                existing_vote.save()
                user_vote = vote_value
        else:
            VideoLike.objects.create(user=request.user, video=video, value=vote_value)
            if vote_value == VideoLike.LIKE:
                video.likes += 1
            else:
                video.dislikes += 1
            user_vote = vote_value

        video.save(update_fields=['likes', 'dislikes'])
        return JsonResponse({
            'success': True,
            'likes': video.likes,
            'dislikes': video.dislikes,
            'user_vote': user_vote
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --- سیستم کامنت ---
@login_required
@require_POST
def add_comment(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    text = request.POST.get('text', '').strip()
    if not text:
        return JsonResponse({'error': 'Comment text is empty'}, status=400)

    comment = Comment.objects.create(video=video, user=request.user, text=text)
    return JsonResponse({
        'success': True,
        'comment': {
            'username': comment.user.username,
            'text': comment.text,
            'created_at': 'Just now',
            'avatar_letter': comment.user.username[0].upper()
        }
    })


# --- صفحه کانال کاربر (فقط نمایش) ---
def channel_videos(request, username):
    channel_user = get_object_or_404(User, username=username)
    videos = Video.objects.filter(user=channel_user).order_by('-created_at')
    profile, created = Profile.objects.get_or_create(user=channel_user)

    is_subscribed = False
    if request.user.is_authenticated:
        is_subscribed = Subscription.objects.filter(
            subscriber=request.user, channel=channel_user
        ).exists()

    sub_count = Subscription.objects.filter(channel=channel_user).count()

    return render(request, 'videos/channel.html', {
        'videos': videos,
        'channel_user': channel_user,
        'profile': profile,
        'is_subscribed': is_subscribed,
        'sub_count': sub_count
    })


# --- سیستم اشتراک (Subscription) ---
@login_required
@require_POST
def toggle_subscribe(request, username):
    """
    Handles subscribing or unsubscribing from a channel.
    """
    channel_user = get_object_or_404(User, username=username)
    subscriber = request.user

    if subscriber == channel_user:
        return JsonResponse({'success': False, 'error': 'You cannot subscribe to yourself.'}, status=400)

    try:
        subscription, created = Subscription.objects.get_or_create(
            subscriber=subscriber,
            channel=channel_user
        )

        if not created:  # If it already existed, it means we are unsubscribing
            subscription.delete()
            is_subscribed = False
            message = f'You have unsubscribed from {channel_user.username}.'
        else:  # It was created, meaning we are subscribing
            is_subscribed = True
            message = f'You have subscribed to {channel_user.username}.'

        # Get the new total subscriber count
        sub_count = Subscription.objects.filter(channel=channel_user).count()

        return JsonResponse({
            'success': True,
            'is_subscribed': is_subscribed,
            'sub_count': sub_count,
            'message': message
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def delete_comment(request, pk):
    try:
        comment = Comment.objects.get(pk=pk)

        if comment.user != request.user:
            return JsonResponse({"error": "Not allowed"}, status=403)

        comment.delete()

        return JsonResponse({"success": True})

    except Comment.DoesNotExist:
        return JsonResponse({"error": "Comment not found"}, status=404)




@staff_member_required
@require_POST
def remove_comment(request, pk):
    try:
        comment = Comment.objects.get(pk=pk)
        comment.delete()

        return JsonResponse({"success": True})

    except Comment.DoesNotExist:
        return JsonResponse({"error": "Comment not found"}, status=404)
