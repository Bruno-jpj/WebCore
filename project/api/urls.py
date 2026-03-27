# this is the file where you define URL routing - mapping URL patterns to views that handle requests

# path('url/', view.view_name, name='view_name')

from django.urls import path
from . import (
    views_api_v1,
    views_api_v2,
    views_api_v3,
    views_api_v31
)

urlpatterns = [
    path('info/v1', views_api_v1.RequestEvent.as_view()),
    path('info/v2', views_api_v2.RequestEvent.as_view()),
    path('info/v3', views_api_v3.RequestEvent.as_view()),
    path('info/v3.1', views_api_v31.RequestEvent.as_view()),
]
