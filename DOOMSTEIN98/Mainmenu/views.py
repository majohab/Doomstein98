from django.shortcuts import render, redirect
from lobby.forms import LobbyForm
from django.urls import reverse
from django.contrib import messages
from lobby.models import Lobby
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required(login_url='/accounts/login/')
def menu(request):
    """Renders HTML document and sends the response.

    Args:
        request (GET): Get menu page.

    Returns:
        HTTP Response: Menu page
    """
    lobbies = Lobby.objects.all()
    context = {'lobbies': lobbies}
    if request.method == "POST":
        form = LobbyForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.add_message(request, messages.SUCCESS,
                                 'Lobby created.')
            return redirect(reverse("menu"))
        else:
            context['lobby_form'] = form
            messages.add_message(request, messages.ERROR,
                                 'Lobby was not created.')
    else:
        form = LobbyForm(request)
        context['lobby_form'] = form
    return render(request, "menu.html",
                  {'form': LobbyForm, 'lobbies': Lobby.objects.all()})

def play(request):
    """Renders HTML document and sends the response.

    Args:
        request (GET): Get start page.

    Returns:
        HTTP Response: Start page
    """
    return render(request, 'play.html', {})
 
def impressum(request):
    """Renders HTML document and sends the response.

    Args:
        request (GET): Get impressum page.

    Returns:
        HTTP Response: Impressum page
    """
    return render(request, 'impressum.html', {})