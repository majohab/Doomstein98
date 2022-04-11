from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views as defined_views
from .forms import UserLoginForm

urlpatterns = [
    path('accounts/login/', defined_views.loginUser, name='login'),
    path('accounts/register/', defined_views.registerUser, name="register"),
    path('accounts/dashboard/', defined_views.dashboard, name="dashboard"),
    path('accounts/activate/<uidb64>/<token>', defined_views.activate_user, name="activate"),
    path('accounts/', include("django.contrib.auth.urls")),
    path('play/', defined_views.play, name="play"),
    path('menu/', defined_views.menu, name="menu"),
]