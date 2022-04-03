from django.urls import path

from . import views

urlpatterns = [
    path('<str:lobby_name>/', views.game, name='game')
]
