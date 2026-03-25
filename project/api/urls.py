# this is the file where you define URL routing - mapping URL patterns to views that handle requests

# path('url/', view.view_name, name='view_name')

from django.urls import path
from . import views
from . import views_base

urlpatterns = [
    path('info/v2', views.RequestEvent.as_view()),
    path('info/v1', views_base.RequestEvent.as_view())
]
