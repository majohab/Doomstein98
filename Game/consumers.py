
import logging
import json


from asgiref.sync import  async_to_sync
from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer
from channels.auth import UserLazyObject
from django.utils.translation import gettext

from .engine import GameEngine

#TODO: Anpassen
MAX_DEGREE = 1000

#TODO: fit that for customized fps
tick_rate = 0.01

log = logging.getLogger(__name__)

#Die serverseitige Spielerklasse
class PlayerConsumer(AsyncWebsocketConsumer):
 
    async def connect(self):

        #If user is unknown
        if self.scope["user"].is_anonymous:
            print("User is unknown. So he has been disconnected")
            await self.close()
        
        self.username = self.scope["user"].user_name

        # Accept the connection with Browser
        await self.accept()

    async def disconnect(self, close_code):
        # Leave game and
        print(F"Disconnect: {close_code}")
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data=None, byte_data=None):
        '''
        Die Daten werden erhalten und in Variablen verpackt, um sie der weiteren Verarbeitung zu übergeben
        '''

        content = json.loads(text_data)

        #Den Message-Typ extrahieren
        msg_type = content["type"]
        msg      = content["msg"]

        #print(content)

        forwarding = {
            "loop"      :  self.validate(msg),
            "joinGame"  :  self.join_game(msg),
            "joinLobby" :  self.join_lobby(msg),
        }

        try:
            return await forwarding[content["type"]]
        except KeyError:
            #Der Typ der Message ist unbekannt
            print(F"Incoming msg {msg_type} is unknown")


    '''Functions which will be commanded to something'''

    async def join_lobby(self, msg):
        
        print(F"Join lobby {msg['lobby']}")

        self.channel_layer = get_channel_layer()
        self.group_name = msg['lobby']

        # Has map already been sent?
        self.map = False

        # Join a common group with all other Players
        await self.channel_layer.group_add(
            self.group_name, 
            self.channel_name
        )


    async def join_game(self, msg: dict):

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "message", 
                "msg": {
                    "message": F"Spieler {self.username} tritt dem Spiel bei", 
                    "channel": self.channel_name,
                },
            },
        )
        
        await self.channel_layer.send(
            "game_engine",
            {
                "type"    : "player.new", 
                "player"  : self.username, 
                "channel" : self.channel_name,
                "lobby"   : msg['lobby'],
            },
        )

        print(self.username + " joining game")

    async def message(self, msg):

        print(F"{msg['msg']['message']} was sent by {msg['msg']['channel']}")

    #Validate movements
    async def validate(self, msg):
        '''
        Die Interaktionen des Spielers werden übertragen
        '''
        
        if not self.username:
            print(F"User {self.username}: Attempting to join game")
            return

        if abs(msg["mouseDeltaX"]) > MAX_DEGREE:
            msg["mouseDeltaX"] = MAX_DEGREE
            print("Mouse change invalid!")

        # If both directions are pressed then dont move in those directions
        msg["y"] = msg["up"] - msg["down"]

        msg["x"] = msg["right"] - msg["left"]

        await self.channel_layer.send(
            "game_engine",
            { 
              "type"    : "player.validate", 
              "player"  : self.username, 
              "msg"     : {
                  "mouseDeltaX" : msg["mouseDeltaX"],
                  "leftClick"   : msg["leftClick"],
                  "y"           : msg["y"],
                  "x"           : msg["x"]
              },
            }
        )
 
    async def game_update(self, event):
        '''
        Send game data to room group after a Tick is processed
        '''

        #print(F"Game Update: {event}")

        # Send message to WebSocket
        state = event["state"]

        if(self.map):
            try:
                state.pop("map")
            except KeyError as e:
                pass
                #print(e)       
        else:
            self.map = True

        #print(state)

        await self.send(json.dumps(state))

class GameConsumer(SyncConsumer): 
    '''
    Class, which can communicate is the game engine channel, specifically it runs the infinite game loop ENGINE of one game
    They communicate through channels.
    '''

    def __init__(self, *args, **kwargs):
        """
        Created on demand when the first player joins.
        """
        print(F"Game Consumer: {args} {kwargs}")
        super().__init__(*args, **kwargs)

        self.channel_layer = get_channel_layer()
        self.engine = {} #The games are saved in there
        self.lobby = {} #What player is in what game

    def player_new(self, event):
        '''
        Join an existing game or Create a new game
        '''

        lobbyname = event['lobby']
        username = event['player']

        print(F"Player {username} joined lobby: {lobbyname}")


        try:
            if len(self.engine[lobbyname].state.players) < self.engine[lobbyname].max_players:
                self.engine[lobbyname].join_game(username)
            else:
                async_to_sync(self.channel_layer.send)(
                event['channel'],
                {
                    "type": "message", 
                    "msg": {
                        "message": F"Es gibt schon zu viele Spieler in der Lobby: {event['lobby']}",
                        "channel": self.channel_name,
                    }, 
                },
            )
        # if the game does not exist, create it
        except KeyError:
            self.engine[lobbyname] = GameEngine(lobbyname)
            self.engine[lobbyname].start()
            self.engine[lobbyname].join_game(username)
            # for further information in what game the player is
            self.lobby[username] = lobbyname

    def player_validate(self, event):

        username = event["player"]

        '''
        Send the data to engine
        '''
        self.engine[self.lobby[username]].apply_events(username, event["msg"])