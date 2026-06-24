from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html'
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page=reverse_lazy('accounts:login')
    ), name='logout'),

    path('register/', views.RegisterView.as_view(
        template_name='accounts/register.html',
        success_url=reverse_lazy('accounts:login')
    ), name='register'),

    path('profile/', views.profile, name='profile'),
    path('subscribe/<str:username>/', views.toggle_subscribe, name='toggle_subscribe'),
    path('subscriptions/', views.subscriptions, name='subscriptions'),
    path('history/', views.history, name='history'),
    path("notification/", views.notifications, name="notification"),

]
