from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from videos.models import Video, Comment
from django.contrib.auth.models import User
from django.contrib import messages
from core.models import Report

from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator
from django.db.models import Q


@staff_member_required
def dashboard_home(request):
    return render(request, "dashboard/home.html")


@staff_member_required
def video_list(request):
    # گرفتن همه ویدیوها از دیتابیس و مرتب‌سازی بر اساس جدیدترین
    videos = Video.objects.all().order_by('-created_at')

    # گرفتن تعداد آیتم در هر صفحه از URL (مثلاً ?per_page=20)
    per_page = request.GET.get("per_page", 10)

    try:
        # تبدیل مقدار به عدد
        per_page = int(per_page)
    except:
        # اگر مقدار اشتباه بود، پیش‌فرض 10 تا در نظر می‌گیریم
        per_page = 10

    # ساخت paginator برای تقسیم ویدیوها به صفحات
    paginator = Paginator(videos, per_page)

    # گرفتن شماره صفحه از URL
    page_number = request.GET.get("page")

    # گرفتن داده‌های همان صفحه (اگر اشتباه باشه خودش اصلاح می‌کنه)
    page_obj = paginator.get_page(page_number)

    # داده‌هایی که به قالب HTML ارسال میشن
    context = {
        "videos": page_obj,  # لیست ویدیوهای همین صفحه
        "page_obj": page_obj,  # اطلاعات کامل pagination (صفحه، تعداد صفحات و ...)
        "per_page": per_page,  # تعداد آیتم در هر صفحه
        "total_videos": videos.count()
    }

    return render(request, 'dashboard/videos.html', context)


@staff_member_required
def comments(request):
    all_comments = (
        Comment.objects
        .select_related("user", "video")
        .order_by("-created_at")
    )

    per_page = request.GET.get("per_page", 10)

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    paginator = Paginator(all_comments, per_page)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "dashboard/comments.html",
        {
            "comments": page_obj,
            "page_obj": page_obj,
            "per_page": per_page,
            "total_comments": all_comments.count(),
        }
    )


@staff_member_required
def delete_comment(request, comment_id):
    # پیدا کردن کامنت با آیدی، اگر نبود ارور 404
    comment = get_object_or_404(Comment, id=comment_id)

    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted successfully.")
        return redirect("dashboard:comments")

    # اگر GET باشد , نمایش صفحه تأیید حذف
    return render(request, "dashboard/delete_comment_confirm.html", {
        "comment": comment
    })


@staff_member_required
def edit_user(request, user_id):
    # گرفتن کاربر از دیتابیس یا 404 اگر وجود نداشت
    user_obj = get_object_or_404(User, id=user_id)

    # اگر فرم ارسال شده باشد (دکمه Save زده شده باشد)
    if request.method == "POST":

        # گرفتن داده‌ها از فرم و حذف فاصله اضافی
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        is_staff = request.POST.get("is_staff") == "on"
        is_active = request.POST.get("is_active") == "on"

        # basic validation
        if not username:
            messages.error(request, "Username cannot be empty.")
            return redirect("dashboard:edit_user", user_id=user_obj.id)

        # prevent duplicate username
        if User.objects.exclude(id=user_obj.id).filter(username=username).exists():
            messages.error(request, "This username already exists.")
            return redirect("dashboard:edit_user", user_id=user_obj.id)

        user_obj.username = username
        user_obj.email = email
        user_obj.is_staff = is_staff
        user_obj.is_active = is_active
        user_obj.save()

        messages.success(request, "User updated successfully.")
        return redirect("dashboard:users")

    return render(request, "dashboard/edit_user.html", {"user_obj": user_obj})


@staff_member_required
def delete_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    # prevent deleting yourself
    if request.user.id == user_obj.id:
        messages.error(request, "You cannot delete your own account.")
        return redirect("dashboard:users")

    if request.method == "POST":
        user_obj.delete()
        messages.success(request, "User deleted successfully.")
        return redirect("dashboard:users")

    return render(request, "dashboard/delete_user_confirm.html", {"user_obj": user_obj})


def users(request):
    # گرفتن متن جستجو از URL (?q=...)
    query = request.GET.get("q", "")
    # گرفتن تعداد آیتم در هر صفحه
    per_page = request.GET.get("per_page", 10)

    try:
        per_page = int(per_page)
    except:
        per_page = 10

    users = User.objects.all().order_by("-date_joined")

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )

    paginator = Paginator(users, per_page)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "query": query,
        "total_users": users.count()
    }

    return render(request, "dashboard/users.html", context)


def report_list(request):
    per_page = int(request.GET.get('per_page', 10))

    reports = Report.objects.all().order_by(
        'is_resolved',
        '-created_at'
    )

    paginator = Paginator(reports, per_page)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'dashboard/reports.html',
        {
            'reports': page_obj,
            'page_obj': page_obj,
            'per_page': per_page,
            "total_reports": reports.count()
        }
    )


def resolve_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    report.is_resolved = True
    report.save()
    return redirect('dashboard:report_list')


@login_required
def report_channel(request, user_id):
    channel_user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        reason = request.POST.get("reason")
        description = request.POST.get("description")

        Report.objects.create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(User),
            object_id=channel_user.id,
            reason=reason,
            description=description
        )

        return JsonResponse({"status": "reported"})

    return JsonResponse({"error": "invalid"}, status=400)


@staff_member_required
def delete_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    if request.method == "POST":
        title = video.title
        video.delete()

        messages.success(
            request,
            f'"{title}" was deleted successfully.'
        )

    return redirect("dashboard:videos")
