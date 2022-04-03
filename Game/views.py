from django.shortcuts import render
from django.http import HttpResponse

def game(request, lobby_name):
    return render(request, 'Game/game.html', {'lobby_name': lobby_name})