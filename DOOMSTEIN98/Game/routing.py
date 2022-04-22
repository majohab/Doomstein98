from django.urls import re_path
from django import setup
import os
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator # Only Host listed in ALLOWED_HOSTS in settings.py are allowed to get access
from django.core.asgi import get_asgi_application

from Game.consumers import GameConsumer, PlayerConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Doomstein98.settings')
asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    [re_path(r'ws/game/(?P<lobby_name>\w+)/$', PlayerConsumer.as_asgi())]
                )
            )
        ),
        "channel": ChannelNameRouter({
            "game_engine": GameConsumer.as_asgi()
        }),
    }
)