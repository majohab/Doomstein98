from django.urls import re_path
import os
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator # Only Host listed in ALLOWED_HOSTS in settings.py are allowed to get access

from Game.consumers import GameConsumer, PlayerConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Doomstein98.settings')

application = ProtocolTypeRouter(
    {
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