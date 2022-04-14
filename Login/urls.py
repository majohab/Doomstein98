from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views as defined_views

urlpatterns = [
    path('accounts/login/', defined_views.loginUser, name='login'),
    path('accounts/register/', defined_views.registerUser, name="register"),
    path('accounts/impressum/', defined_views.impressum, name="impressum"),
    path('accounts/privacy/', defined_views.privacy, name="privacy"),
    path('accounts/activate/<uidb64>/<token>', defined_views.activate_user, name="activate"),
    path('accounts/', include("django.contrib.auth.urls")),
    path('play/', defined_views.play, name="play"),
]