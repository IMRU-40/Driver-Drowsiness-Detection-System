from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('',views.generate_hist,name="generate_hist"),
]
