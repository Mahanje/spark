# spark/views.py
from django.shortcuts import render
from django.http import HttpResponse
import os
from django.conf import settings

# ... (بقیه view های شما)

def service_worker(request):
    """
    این View فایل sw.js را از پوشه templates می‌خواند و به عنوان application/javascript برمی‌گرداند.
    """
    # مسیر فایل sw.js را بر اساس تنظیمات پروژه تعیین می‌کنیم
    # settings.BASE_DIR به ریشه اصلی پروژه اشاره دارد (جایی که manage.py قرار دارد)
    file_path = os.path.join(settings.BASE_DIR, 'templates', 'sw.js')

    try:
        # فایل را باز می‌کنیم و محتوای آن را می‌خوانیم
        with open(file_path, 'r', encoding='utf-8') as f:
            sw_code = f.read()
        # محتوای فایل را به عنوان پاسخ HttpResponse برمی‌گردانیم
        # content_type باید application/javascript باشد تا مرورگر آن را به عنوان کد جاوا اسکریپت بشناسد
        return HttpResponse(sw_code, content_type='application/javascript')
    except FileNotFoundError:
        # اگر فایل پیدا نشد، یک پاسخ خطا برمی‌گردانیم
        print(f"Error: Service worker file not found at {file_path}") # برای دیباگ در کنسول سرور
        return HttpResponse("Service worker file not found.", status=404)
    except Exception as e:
        # برای خطاهای احتمالی دیگر
        print(f"Error reading service worker file: {e}") # برای دیباگ
        return HttpResponse("Error serving service worker file.", status=500)

