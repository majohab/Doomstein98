from django.http import JsonResponse
from django.shortcuts import render
from os import path 

def game(request, lobby_name):
    return render(request, 'Game/game.html', {'lobby_name': lobby_name})

def get_sprite_name(request, sprite_name):
    with open(
            path.join(path.dirname(__file__), "C:/Users/lasse/OneDrive - Duale Hochschule Baden-Württemberg Stuttgart/StudyFiles/Fächer/Semester 4/Web/Doomstein98/Game/textures/" + sprite_name + ".bmp")
            , "rb") as image:
        f = image.read()
        b = bytearray(f)
        s = ''.join('{:02x}'.format(x) for x in b)
        print(s)
        return JsonResponse({"sprite_string" : s}, status=200)