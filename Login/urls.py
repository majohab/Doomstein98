from django.urls import path, include
from . import views

urlpatterns = [
    path('accounts/', include("django.contrib.auth.urls")),
    path('play/', views.play, name="play"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('menu/', views.menu, name="menu"),
    path('register/', views.register, name="register"),
    path('impressum/', views.impressum, name="impressum"),
    path('privacy/', views.privacy, name="privacy")
]