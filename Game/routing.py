from django.urls import re_path
import os
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack

from Game.consumers import GameConsumer, PlayerConsumer


from . import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Doomstein98.settings')

#websocket_urlpatterns = [
#    re_path(r'ws/game/(?P<lobby_name>\w+)/$', consumers.PlayerConsumer.as_asgi()),
#]

application = ProtocolTypeRouter(
    {
        "websocket": SessionMiddlewareStack(URLRouter([re_path(r'ws/game/(?P<lobby_name>\w+)/$', PlayerConsumer)])),
        "channel": ChannelNameRouter({"game_engine": GameConsumer}),
    }
)
