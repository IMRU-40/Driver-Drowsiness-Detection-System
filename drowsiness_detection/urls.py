from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name="home"),
    path('detect_drowsiness/',views.detect_drowsiness,name="detect_drowsiness"),
    path('video_feed', views.video_feed, name='video_feed'),
]
