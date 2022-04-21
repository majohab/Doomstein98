
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
TICK_RATE = 0.01

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
        #print(F"Disconnect: {close_code}")
        try:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        except:
            pass
    
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
        self.map = 0


    async def join_game(self, msg: dict):

        # Add the player to the channel from which the information will be recieved about the status
        # Join a common group with all other Players
        await self.channel_layer.group_add(
            self.group_name, 
            self.channel_name
        )

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
                "type"    : "new.player", 
                "player"  : self.username, 
                "channel" : self.channel_name,
                "lobby"   : msg['lobby'],
            },
        )

        #print(self.username + " joining game")


    async def message(self, msg):

        print(F"{msg['msg']['message']} was sent by {msg['msg']['channel']}")

    #Validate movements
    async def validate(self, msg):
        '''
        Die Interaktionen des Spielers werden übertragen
        '''
        
        if not self.username:
            #print(F"User {self.username}: Attempting to join game")
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
              "type"    : "validate.event", 
              "player"  : self.username, 
              "msg"     : {
                  "mouseDeltaX" : msg["mouseDeltaX"],
                  "leftClick"   : msg["leftClick"],
                  "y"           : msg["y"],
                  "x"           : msg["x"],
                  "weapon"      : msg["weapon"]
              },
            }
        )
 
    async def game_update(self, event):
        '''
        Send game data to room group after a Tick is processed
        '''

        #print(F"Game Update: {event}")

        # Send message to WebSocket
        event = event["state"]

        event["type"] = "update"

        if(self.map > 10):
            try:
                event.pop("map")
            except KeyError as e:
                pass       
        else:
            self.map += 1

        #print(event)

        await self.send(json.dumps(event))

    async def win(self, event):
        '''
        Check if current player won the game and forward the message to player
        '''
        event["type"] = "loose"

        for player in event["players"]:

            if player["name"] == self.username:

                event["type"] = "win"

        await self.send(json.dumps(event))



class GameConsumer(SyncConsumer): 
    '''
    Class, which can communicate is the game engine channel, specifically it runs the infinite game loop ENGINE of one game
    They communicate through channels.
    '''

    def __init__(self, *args, **kwargs):
        """
        Created on demand when the first player joins.
        """
        super().__init__(*args, **kwargs)

        self.channel_layer = get_channel_layer()
        self.engines : dict[GameEngine] = {} #The games are saved in there
        self.lobbies = {} #What player is in what game

    def new_player(self, event):
        '''
        Join an existing game or Create a new game
        '''

        lobbyname = event['lobby']
        username = event['player']

        print(F"Player {username} joined lobby: {lobbyname}")

        # for further information in what game the player is
        self.lobbies[username] = lobbyname 

        try:
            if len(self.engines[lobbyname].state.players) < self.engines[lobbyname].max_players:
                self.engines[lobbyname].join_game(username)
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

            self.engines[lobbyname] = GameEngine(lobbyname)
            self.engines[lobbyname].start()
            self.engines[lobbyname].join_game(username)

            #TODO: Only for TESTING
            self.engines[lobbyname].start_flag = True


    def validate_event(self, event):

        username = event["player"]

        '''
        Send the data to engine
        '''
        self.engines[self.lobbies[username]].apply_events(username, event["msg"])

    def win(self, event):
        '''
        handling when game is finished
        '''
        group_name = event["group"]

        # Stop the thread by ending its tasks
        self.engines[group_name].running = False

        # Synchronize the channel's information and send them to all participants
        async_to_sync(self.channel_layer.group_send)(
            group_name, 
            {
             "type"   : "win",
             "time"   : event["time"],
             "players": event["players"],  
            }
        )

        




