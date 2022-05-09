from django.urls import path

from . import views

urlpatterns = [
    path('<str:lobby_name>/', views.game, name='game'),
    path('getSprite/<str:sprite_name>/', views.get_sprite_name, name='sprite')
]
