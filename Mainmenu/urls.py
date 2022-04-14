from django.urls import path, include
from . import  views

urlpatterns = [
    path('lobby/', views.lobby, name="lobby"),
]