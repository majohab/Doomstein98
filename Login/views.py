from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from Login.forms import CustomUserCreationForm

# Create your views here.
def play(request):
    return render(request, 'play.html', {})

def dashboard(request):
    return render(request, 'dashboard.html', {})

@login_required(login_url='/accounts/login/')
def menu(request):
    return render(request, 'menu.html', {})

def register(request):
    if request.method == "GET":
        return render(
            request, "Login/register.html",
            {"form": CustomUserCreationForm}
        )
    elif request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse("dashboard"))

def impressum(request):
    return render(request, 'impressum.html', {})

def privacy(request):
    return render(request, 'privacy.html', {}) 
