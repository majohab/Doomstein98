from django.urls import path
from . import views as defined_views

# register your urls

urlpatterns = [
    path('', defined_views.LobbyForm, name="lobby"),
]