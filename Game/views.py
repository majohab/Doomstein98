from django.http import JsonResponse
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from os import path

def game(request, lobby_name):
    return render(request, 'gamewindow.html', {'lobby_name': lobby_name})

def get_sprite_name(request, sprite_name):
    with open(
            path.join(settings.BASE_DIR, "Game/textures/" + sprite_name + ".bmp")
            , "rb") as image:
        f = image.read()
        b = bytearray(f)
        s = ''.join('{:02x}'.format(x) for x in b)
        return JsonResponse({"sprite_string" : s}, status=200)