from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views as defined_views
from .forms import UserLoginForm

urlpatterns = [
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html', authentication_form=UserLoginForm), name='login'),
    path('accounts/register/', defined_views.register, name="register"),
    path('accounts/dashboard/', defined_views.dashboard, name="dashboard"),
    path('accounts/', include("django.contrib.auth.urls")),
    path('play/', defined_views.play, name="play"),
    path('menu/', defined_views.menu, name="menu"),
]