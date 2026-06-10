# spark/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views # این خط رو نگه دار چون برای service_worker نیاز داری

urlpatterns = [
    path('admin/', admin.site.urls),

    #PWA
    path('sw.js', views.service_worker, name='service_worker'),

    #accounts
    path('accounts/', include('accounts.urls')),

    #videos
    path('', include('videos.urls')),

    #dashboard
    path("dashboard/", include("dashboard.urls")),

    #core
    path("core/" , include("core.urls"))

]

# این بخش رو تغییر بده:
if settings.DEBUG:
    # این خط فایل های استاتیک رو سرو میکنه
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # این خط فایل های مدیا رو سرو میکنه (که از قبل داشتی)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)