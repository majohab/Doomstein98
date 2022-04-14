from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from Login.forms import CustomUserCreationForm

# Create your views here.

def lobby(request):
    return render(request, 'lobby.html', {})