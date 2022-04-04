from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from Login.forms import RegistrationForm

# Create your views here.
def play(request):
    return render(request, 'play.html', {})

def dashboard(request):
    return render(request, 'dashboard.html', {})

@login_required(login_url='/accounts/login/')
def menu(request):
    return render(request, 'menu.html', {})

def register(request):
    context = {}
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            authenticate(email=form.cleaned_data.get('email'), password=form.cleaned_data.get('password1'))
            login(request, user)
            return redirect(reverse("dashboard"))
        else:
            context['registration_form'] = form
    else:
        form = RegistrationForm()
        context['registration_form'] = form
    return render(
        request, "registration/register.html",
        {"form": RegistrationForm}
    )