from django.urls import path
from . import views

urlpatterns = [
    path('info/', views.RequestEvent.as_view()),
]
