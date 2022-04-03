"""
ASGI config for Doomstein98 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os
import django

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from django.core.asgi import get_asgi_application

import Game.routing

django.setup()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Doomstein98.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            Game.routing.websocket_urlpatterns
        )
    )
})