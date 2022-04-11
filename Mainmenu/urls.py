from django.urls import path
from . import views as defined_views

urlpatterns = [
    path('', defined_views.menu, name="menu"),
]