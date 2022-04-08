
import logging
import json
import time

from asgiref.sync import  async_to_sync
from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer

from .engine import GameEngine

#TODO: Anpassen
MAX_DEGREE = 360

log = logging.getLogger(__name__)

#Die serverseitige Spielerklasse
class PlayerConsumer(AsyncWebsocketConsumer):
 
    async def connect(self):
        """
        Perform things on connection start
        """
        print("Connect")
        self.channel_layer = get_channel_layer()
        self.group_name = "doom_game"
        self.game = None
        self.username = None

        # Countdown for mouse restriction
        self.mouseClicked = 0

        # Has map already been sent?
        self.map = False

        # Join a common group with all other Players
        await self.channel_layer.group_add(
            self.group_name, 
            self.channel_name
        )
        print("User connected successfully")

        # Accept the connection with Browser
        await self.accept()

    async def disconnect(self, close_code):
        # Leave game and
        print(F"Disconnect: {close_code}")
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def join(self, msg: dict):

        self.username = msg["username"]

        print("join wurde mit der msg " + msg["username"] + " aufgerufen\n\n",)

        #if "username" not in self.scope["session"]:
        #    self.scope["session"]["username"] = username
        #    self.scope["session"].save()

        #self.username = self.scope["session"]["username"]

        await self.channel_layer.send(
            self.group_name,
            {
                "type": "message", 
                "message": "Spieler " + self.username + " tritt dem Spiel bei", 
                "channel": self.channel_name
            },
        )
        
        await self.channel_layer.send(
            "game_engine",
            {
                "type": "player.new", 
                "player": self.username, 
                "channel": self.channel_name
            },
        )

        print("User: " + self.username + " joining game")

    async def message(self, msg):
        print(msg)

    #Die Interaktionen des Spielers werden übertragen
    async def forward(self, msg):

        self.mouseClicked -= 1

        if not self.username:
            print(F"User {self.username}: Attempting to join game")
            return
        
        print(F"User {self.username}: {msg}")

        await self.channel_layer.send(
            "game_engine",
            { 
              "type"    : "player.validate", 
              "player"  : self.username, 
              "msg"     : msg,
            }
        )
 
    #Die Daten werden erhalten und in Variablen verpackt, um sie der weiteren Verarbeitung zu übergeben
    async def receive(self, text_data=None, byte_data=None):

        content = json.loads(text_data)

        #print(content)

        #Den Message-Typ extrahieren
        msg_type = content["type"]
        msg      = content["msg"]

        #Was soll bei verschiedenen Message-Typen passieren?
        if msg_type == "loop":
            return await self.forward(msg)
        elif msg_type == "join":
            return await self.join(msg)
        else:
            #Der Typ der Message ist unbekannt
            print(F"Incoming msg {msg_type} is unknown")

    # Send game data to room group after a Tick is processed
    async def game_update(self, event):

        #print(F"Game Update: {event}")

        # Send message to WebSocket
        state = event["state"]

        if(self.map):
            try:
                state.pop("map")
            except KeyError as e:
                print(e)       
        else:
            self.map = True

        await self.send(json.dumps(state))
 
# Class, which can communicate with the game engine, specifically it runs the infinite game loop ENGINE
# They communicate through channels
class GameConsumer(SyncConsumer): 

    def __init__(self, *args, **kwargs):
        """
        Created on demand when the first player joins.
        """
        print(F"Game Consumer: {args} {kwargs}")
        super().__init__(*args, **kwargs)
        self.group_name = "doom_game"
        self.engine = GameEngine(self.group_name)
        self.engine.start()

    def player_new(self, event):
        print("Player Joined: " + event["player"] )
        self.engine.join_game(event["player"])

    def player_validate(self, event):
        
        #print(F"Player changed: {event}")
        
        # If the mouse was recently pressed, ignore that click
        #if(event["msg"]["LeftClick"] == True and self.mouseClicked > 0):
        #    event["msg"]["LeftClick"] = False
        #    print("Too often clicked!")

        #elif(event["msg"]["LeftClick"] == True and self.mouseClicked == 0):
        #    self.mouseClicked = 10
        #    print("Click was successful!")

        # If both directions are pressed then dont move in those directions
        event["msg"]["y"] = event["msg"]["up"] - event["msg"]["down"]

        event["msg"]["x"] = event["msg"]["right"] - event["msg"]["left"]

        print(event["msg"])

        if event["msg"]["mouseDeltaX"] > MAX_DEGREE:
            event["msg"]["mouseDeltaX"] = MAX_DEGREE
            print("Mouse change invalid!")

        '''
        Send the data to engine
        '''
        self.engine.apply_events(event["player"], event["msg"])