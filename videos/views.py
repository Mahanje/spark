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



def video_detail(request, video_id):

    # ویدیو را از دیتابیس پیدا می‌کند
    video = get_object_or_404(Video, pk=video_id)

    # افزایش بازدید به صورت اتمیک و سریع
    Video.objects.filter(pk=video_id).update(views=F('views') + 1)
    video.views += 1  # این خط باعث می‌شود عدد جدید در همین لحظه در صفحه نمایش داده شود

    is_subscribed = False
    if request.user.is_authenticated:
        # آیا کاربر فعلی سابسکرایبر صاحب این ویدیو هست؟
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
    # پارامتر q را از URL می‌گیرد
    query = request.GET.get('q')

    if query:
        # جستجوی هوشمند در عنوان ویدیو و نام کاربری سازنده (کانال)
        videos = Video.objects.filter(
            Q(title__icontains=query) | #or
            Q(user__username__icontains=query)
        ).distinct().order_by('-created_at') #distinct برای حذف نتایج تکراری
    else:
        # نمایش همه ویدیوها در حالت عادی
        videos = Video.objects.all().order_by('-created_at')

    return render(request, 'videos/list.html', {'videos': videos, 'query': query})


# --- آپلود ویدیو ---
@login_required
@require_POST
def video_upload(request):
    # ساخت فرم و پر کردن آن با داده‌های ارسال شده
    form = VideoUploadForm(request.POST, request.FILES)

    # اعتبارسنجی فرم
    if not form.is_valid():
        return JsonResponse(
            {'error': 'Invalid form data'},
            status=400
        )

    try:
        # گرفتن فایل ویدیو از فرم
        video_file = request.FILES.get('video_file')

        # اگر فایل ویدیو اپلود نشده باشد
        if not video_file:
            return JsonResponse(
                {'error': 'No video file provided'},
                status=400
            )

        # حداکثر 10 مگابایت
        if video_file.size > 10 * 1024 * 1024:
            return JsonResponse(
                {'error': 'Video size must be less than 10 MB'},
                status=400
            )

        # آپلود ویدیو در ImageKit
        video_data = upload_video(
            file_data=video_file.read(), # تبدیل فایل به bytes
            file_name=video_file.name
        )

        # مقدار پیش‌فرض برای تامبنیل
        thumbnail_url = ""

        thumbnail_file = request.FILES.get('thumbnail_file')

        if thumbnail_file:
            thumb_res = upload_thumbnail(
                file_data=thumbnail_file.read(),
                file_name=thumbnail_file.name
            )
            # ذخیره لینک تامبنیل
            thumbnail_url = thumb_res["url"]

        # ساخت رکورد ویدیو در دیتابیس
        video = Video.objects.create(
            user=request.user,
            title=form.cleaned_data['title'],
            description=form.cleaned_data['description'],
            file_id=video_data['file_id'],
            video_url=video_data['url'],
            thumbnail_url=thumbnail_url,
        )

        return JsonResponse({
            'success': True,
            'video_id': video.id
        })

    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=500
        )


# --- سیستم لایک و دیسلایک ---
@login_required
@require_POST
def video_vote(request, video_id):
    #  پیدا کردن ویدیو و گرفتن ان از دیتابیس
    video = get_object_or_404(Video, id=video_id)
    try:
        # مقدار رأی ارسال شده از فرانت
        vote_value = int(request.POST.get('vote'))
        # آیا کاربر لاگین شده قبلاً روی این ویدیو رأی داده؟
        # اولین رکوردی که QuerySet پیدا کرده را برگردان، و اگر چیزی پیدا نشد None برگردان.
        existing_vote = VideoLike.objects.filter(user=request.user, video=video).first()
        # فرض می‌کنیم کاربر هیچ رأی فعالی ندارد
        user_vote = None

        # اگر قبلاً رأی داده باشد
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
    text = request.POST.get('text', '').strip() #فاصله‌های اول و آخر را حذف می‌کند
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


@login_required
@require_POST
def delete_video(request, video_id):
    video = get_object_or_404(
        Video,
        id=video_id,
        user=request.user
    )

    try:
        ik_delete_video(video.file_id)
        video.delete()

        return JsonResponse({
            'success': True,
            'message': 'Video deleted successfully'
        })

    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=500
        )



@login_required
def video_upload_page(request):
    return render(
        request,
        'videos/upload.html',
        {'form': VideoUploadForm()}
    )