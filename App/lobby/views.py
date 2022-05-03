from django.shortcuts import render
from .forms import LobbyForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse

# Create your views here.

def createLobby(request):
    """Form to create a new lobby

    Args:
        request (GET): HTML page

    Returns:
        HTTP Response: Lobby creation form
    """
    context = {}
    if request.method == "POST":
        form = LobbyForm(request.POST)
        if form.is_valid():
            lobby = form.save()
            messages.add_message(request, messages.SUCCESS,
                                 'The lobby was created.')
            return redirect(reverse("lobby"))
        else:
            context['lobby_form'] = form
            messages.add_message(request, messages.ERROR,
                                 'Lobby was not created try again.')
    else:
        form = LobbyForm(request)
        context['lobby_form'] = form
    return render(request, "lobby.html",
                  {"form": LobbyForm})
