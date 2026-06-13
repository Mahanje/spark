from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('report/submit/', views.submit_report, name='submit_report'),
]
