from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    path('', views.video_list, name='list'),
    path('video/<int:video_id>/', views.video_detail, name='detail'),

    # صفحه فرم آپلود
    path('upload/', views.video_upload_page, name='upload'),
    # پردازش submit آپلود
    path('upload/submit/', views.video_upload, name='upload_submit'),

    path('channel/<str:username>/', views.channel_videos, name='channel'),
    path('video/<int:video_id>/vote/', views.video_vote, name='video_vote'),
    path('video/<int:video_id>/delete/', views.delete_video, name='delete_video'),
    path('video/<int:video_id>/comment/', views.add_comment, name='add_comment'),
    path('search/', views.search_videos, name='search'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
    path('comment/<int:pk>/remove/', views.remove_comment, name='remove_comment'),
    path("videos/edit/<int:video_id>/", views.edit_video, name="edit_video"),
]
