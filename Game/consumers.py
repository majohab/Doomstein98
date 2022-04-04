
import logging
import json

from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncWebsocketConsumer

from .engine import GameEngine

MAX_DEGREE = 20

log = logging.getLogger(__name__)

#Die serverseitige Spielerklasse
class PlayerConsumer(AsyncWebsocketConsumer):

    mouseClicked = 0
 
    async def connect(self):
        """
        Perform things on connection start
        """
        print("Connect")
        self.group_name = "doom_game"
        self.game = None
        self.username = None
        print("User connected successfully")

        # Join a common group with all other Players
        await self.channel_layer.group_add(
            self.group_name, 
            self.channel_name
        )

        # Accept the connection with Browser
        await self.accept()

    async def disconnect(self, close_code):
        # Leave game and
        print("Disconnect: %s", close_code)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def join(self, msg: dict):

        self.username = msg["username"]

        #print("join wurde mit der msg " + msg["username"] + " aufgerufen\n\n",)

        #if "username" not in self.scope["session"]:
        #    self.scope["session"]["username"] = username
        #    self.scope["session"].save()

        #self.username = self.scope["session"]["username"]

        #print(self.channel_name)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "bsp_message", 
                "message": self.username, 
                "channel": self.channel_name
            },
        )

        print("User: " + self.username + " joining game")
        
        await self.channel_layer.group_send(
            "game_engine",
            {
                "type": "player.new", 
                "player": self.username, 
                "channel": self.channel_name
            },
        )

        print(self.channel_layer)

    async def forward(self, msg):

        self.mouseClicked -= 1

        if not self.username:
            print("User %s: Attempting to join game", self.username)
            return
        
        print("User %s: %s", self.username, msg)

        await self.channel_layer.send(
            "game_engine",
            { 
              "type"    : "player.validate", 
              "player"  : self.username, 
              "msg"     : msg,
            }
        )
 
    #Die Daten werden erhalten und in Variablen verpackt, um sie der weiteren Verarbeitung zu übergeben
    async def receive(self, text_data=None):

        print("\n" + text_data + ": wurde gesendet!")

        #Die Daten als Json behandeln
        content = json.loads(text_data)

        #Den Message-Typ extrahieren
        msg_type = content["type"]
        msg      = content["msg"]

        #Was soll bei verschiedenen Message-Typen passieren?
        if msg_type == "loop":
            return await self.validate(msg)
        elif msg_type == "join":
            print("\n\nEin Spieler möchten beitreten\n")
            
            return await self.join(msg)
        else:
            #Der Typ der Message ist unbekannt
            print("Incoming msg %s is unknown", msg_type)
 
    async def bsp_message(self, event):
        print("HUNDESOHN!!\n")

    # Send game data to room group after a Tick is processed
    async def game_update(self, event):

        print("Game Update: %s", event)

        # Send message to WebSocket
        state = event["state"]
        await self.send(json.dumps(state))   
 
# Class, which can communicate with the game engine, specifically it runs the infinite game loop ENGINE
# They communicate through channels
class GameConsumer(SyncConsumer): 
    
    def __init__(self, *args, **kwargs):
        """
        Created on demand when the first player joins.
        """
        print("Game Consumer: %s %s", args, kwargs)
        super().__init__(*args, **kwargs)
        self.group_name = "game_engine"
        self.engine = GameEngine(self.group_name)
        self.engine.start()

    def player_new(self, event):

        print("Player Joined: %s", event["player"])
        self.engine.join_game(event["player"])

    def player_validate(self, event):
        
        print("Player changed: %s", event)
        
                # If the mouse was recently pressed, ignore that click
        if(event["msg"]["LeftClick"] == True and self.mouseClicked > 0):
            event["msg"]["LeftClick"] = False
            print("Too often clicked!")

        elif(event["msg"]["LeftClick"] == True and self.mouseClicked == 0):
            self.mouseClicked = 10
            print("Click was successful!")

        # If both directions are pressed then dont move in those directions
        if event["msg"]["Up"] == True and event["msg"]["Down"] == True:
            event["msg"]["Up"] = False
            event["msg"]["Down"] = False
            print("Opposite key were pressed!")

        # If both directions are pressed then dont move in those directions
        if event["msg"]["Left"] == True and event["msg"]["Right"] == True:
            event["msg"]["Left"] = False
            event["msg"]["Right"] = False
            print("Opposite key were pressed!")

        if event["msg"]["MouseX"] > MAX_DEGREE:
            event["msg"]["MouseX"] = MAX_DEGREE
            print("Mouse change invalid!")

        if event["msg"]["MouseY"] > MAX_DEGREE:    
            event["msg"]["MouseY"] = MAX_DEGREE
            print("Mouse cahnge invalid!")

        # Send the data to 
        self.engine.apply_events(event["player"], event["msg"])