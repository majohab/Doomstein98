from django.urls import path
from . import  views

urlpatterns = [
    path('', views.play, name="play"),
    path('play/', views.play, name="play"),
    path('menu/', views.menu, name="menu"),
    path('impressum/', views.impressum, name="impressum"),
]