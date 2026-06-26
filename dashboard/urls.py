from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path('', views.dashboard_home, name="home"),
    path('users/', views.users, name="users"),
    path("users/<int:user_id>/edit/", views.edit_user, name="edit_user"),
    path("users/<int:user_id>/delete/", views.delete_user, name="delete_user"),
    path('videos/', views.video_list, name="videos"),
    path("videos/<int:video_id>/delete/", views.delete_video, name="delete_video", ),
    path('comments/', views.comments, name="comments"),
    path("comments/delete/<int:comment_id>/", views.delete_comment, name="delete_comment"),
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:pk>/resolve/', views.resolve_report, name='resolve_report'),
    path("channel/<int:user_id>report/", views.report_channel, name="report_channel"),
]
