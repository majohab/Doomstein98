
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
        log.info("Connect")
        self.group_name = "Doomstein"
        self.game = None
        self.username = None
        log.info("User connected successfully")

        # Join a common group with all other Players
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        # Accept the connection with Browser
        await self.accept()

    async def disconnect(self, close_code):
        # Leave game and
        log.info("Disconnect: %s", close_code)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def join(self, msg: dict):

        username = msg["username"]

        if "username" not in self.scope["session"]:
            self.scope["session"]["username"] = username
            self.scope["session"].save()

        self.username = self.scope["session"]["username"]

        log.info("User %s: Joining game", self.username)
        await self.channel_layer.send(
            "game_engine",
            {"type": "player.new", "player": self.username, "channel": self.channel_name},
        )

    async def forward(self, msg):

        self.mouseClicked -= 1

        if not self.username:
            log.info("User %s: Attempting to join game", self.username)
            return
        
        log.info("User %s: %s", self.username, msg)

        await self.channel_layer.send(
            "game_engine",
            { 
              "type"    : "player.validate", 
              "player"  : self.username, 
              "msg"     : msg,
            }
        )
 
    #Die Daten werden erhalten und in Variablen verpackt, um sie der weiteren Verarbeitung zu übergeben
    async def receive(self, text_data=None, bytes_data=None):

        #Die Daten als Json behandeln
        content = json.loads(text_data)

        #Den Message-Typ extrahieren
        msg_type = content["type"]
        msg      = content["msg"]

        #Was soll bei verschiedenen Message-Typen passieren?
        if msg_type == "loop":
            return await self.validate(msg)
        elif msg_type == "join":
            return await self.join(msg)
        else:
            #Der Typ der Message ist unbekannt
            log.warn("Incoming msg %s is unknown", msg_type)
 
    # Send game data to room group after a Tick is processed
    async def game_update(self, event):

        log.info("Game Update: %s", event)

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
        log.info("Game Consumer: %s %s", args, kwargs)
        super().__init__(*args, **kwargs)
        self.group_name = "doomstein_game"
        self.engine = GameEngine(self.group_name)
        self.engine.start()

    #def player_new(self, event):
   #     log.info("Player Joined: %s", event["player"])
   #     self.engine.join_queue(event["player"])


    #########################################################
    ##### hier die ganzen Daten übertragen
    ##### TODO: Einzelne Funktionen zur Weitergabe validieren
    ####        Sind die Inputs valide? Kann man den Daten trauen?
    ####        Formattiere wandle diese Daten um
    #########################################################

    def player_validate(self, event):
        
        log.info("Player changed: %s", event)
        
                # If the mouse was recently pressed, ignore that click
        if(event["msg"]["LeftClick"] == True and self.mouseClicked > 0):
            event["msg"]["LeftClick"] = False
            log.info("Too often clicked!")

        elif(event["msg"]["LeftClick"] == True and self.mouseClicked == 0):
            self.mouseClicked = 10
            log.info("Click was successful!")

        # If both directions are pressed then dont move in those directions
        if event["msg"]["Up"] == True and event["msg"]["Down"] == True:
            event["msg"]["Up"] = False
            event["msg"]["Down"] = False
            log.info("Opposite key were pressed!")

        # If both directions are pressed then dont move in those directions
        if event["msg"]["Left"] == True and event["msg"]["Right"] == True:
            event["msg"]["Left"] = False
            event["msg"]["Right"] = False
            log.info("Opposite key were pressed!")

        if event["msg"]["MouseX"] > MAX_DEGREE:
            event["msg"]["MouseX"] = MAX_DEGREE
            log.info("Mouse change invalid!")

        if event["msg"]["MouseY"] > MAX_DEGREE:    
            event["msg"]["MouseY"] = MAX_DEGREE
            log.info("Mouse cahnge invalid!")

        #Die Spielerrichtung weitergeben
        self.engine.apply_events(event["player"], event["msg"])