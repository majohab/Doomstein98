from sre_constants import SUCCESS
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views as defined_views

urlpatterns = [
    path('login/', defined_views.loginUser, name='login'),
    path('register/', defined_views.registerUser, name="register"),
    path('privacy/', defined_views.privacy, name="privacy"),
    path('activate/<uidb64>/<token>', defined_views.activate_user, name="activate"),
    path('', include("django.contrib.auth.urls")),
    path('changepassword/', auth_views.PasswordChangeView.as_view(template_name='user.html', success_url='/menu'), name="changepassword"),
]