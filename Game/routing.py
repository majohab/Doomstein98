from django.urls import re_path
import os
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack

from Game.consumers import GameConsumer, PlayerConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Doomstein98.settings')

application = ProtocolTypeRouter(
    {
        "websocket": SessionMiddlewareStack(URLRouter([re_path(r'ws/game/(?P<lobby_name>\w+)/$', PlayerConsumer.as_asgi())])),
        "channel": ChannelNameRouter({
            "game_engine": GameConsumer.as_asgi()
        }),
    }
)