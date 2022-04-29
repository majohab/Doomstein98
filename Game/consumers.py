
import logging
import json

from asgiref.sync               import  async_to_sync
from channels.consumer          import SyncConsumer
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from channels.layers            import get_channel_layer
from lobby.models               import Lobby
from channels.db                import database_sync_to_async

from .engine import GameEngine

#TODO: Anpassen
MAX_DEGREE = 300

#TODO: fit that for customized fps
TICK_RATE = 1/60

log = logging.getLogger(__name__)

#Key Constants
channel_key    = 'c'
click_key      = 'c'
down_key       = 'd'
group_key      = 'g'
inactive_key   = 'i'
left_key       = 'l'
loose_key      = 'l'
lobby_key      = 'l'
mouseDelta_key = 'm'
message_key    = 'm'
map_key        = 'm'
name_key       = 'n'
player_key     = 'p'
right_key      = 'r'
state_key      = 's'
time_key       = 't'
type_key       = 't'
update_key     = 'u'
up_key         = 'u'
weapon_key     = 'w'
win_key        = 'w'
joinLobby_key  = 'jL'
joinGame_key   = 'jG' 

class PlayerConsumer(AsyncWebsocketConsumer):
    '''
    The asynchronous player class which handles the incoming messages from the client
    And send the messages to the client back
    '''

    @database_sync_to_async
    def get_lobby(self, lobbyName):

        return Lobby.objects.get(name=lobbyName)

    def write_lobby(self, var, data):

        return
 
    '''
    Connect the client with the server
    '''
    async def connect(self):

        #If user is unknown
        if self.scope["user"].is_anonymous:
            print("User is unknown. So he has been disconnected")
            await self.close()
        
        self.username = self.scope["user"].user_name

        # Accept the connection with Browser
        await self.accept()

    '''
    Disconnect the player from the lobby if he has no connection anymore
    '''
    async def disconnect(self, close_code):

        try:
            print(F"Disconnect: {close_code}")
            await self.channelLayer.group_discard(
                self.groupName,
                self.channel_name
            )
        except:
            pass
    
    '''
    If the client sent something
    '''
    async def receive(self, text_data=None, byte_data=None):
        '''
        Die Daten werden erhalten und in Variablen verpackt, um sie der weiteren Verarbeitung zu übergeben
        '''

        content = json.loads(text_data)

        #print(content)

        #Den Message-Typ extrahieren
        msg_type = content[type_key]
        msg      = content[message_key]

        #print(content)

        forwarding = {
            update_key    :  self.validate(msg),
            joinLobby_key :  self.join_lobby(msg),
        }

        try:
            return await forwarding[content[type_key]]
        except KeyError:
            #Der Typ der Message ist unbekannt
            print(F"Incoming msg {msg_type} is unknown")


    '''Functions which will be commanded to something'''


    async def join_lobby(self, msg):

        try:
            #if there is a lobby
            lobby = await self.get_lobby(msg[lobby_key])
            print(F"Join lobby {lobby.name}")

            try:
                self.scope["lobby"]
            except:
                #Default value
                self.scope["lobby"] = ""

            # If the max player was reached and the player is not currently in the game
            if(lobby.current_players >= lobby.max_players and not lobby.name in self.scope["user"]["lobby"]):
                print(F"Too many players in Lobby {lobby.name}")
                await self.close()
            else:
                self.channelLayer = get_channel_layer()
                self.groupName = msg[lobby_key]

                # Has map already been sent?
                self.map = 0

                #print(F"Joining {self.channel_name}")

                # Add the player to the channel from which the information will be recieved about the status
                # Join a common group with all other Players
                await self.channelLayer.group_add(
                    self.groupName, 
                    self.channel_name
                )

                await self.channelLayer.send(
                    "game_engine",
                    {
                        "type"       : "new.player", # execute new_player() 
                        player_key   : self.username, 
                        channel_key  : self.channel_name, #channel
                        lobby_key    : msg[lobby_key], #lobby
                    },
                )
        except:
            print(F"There is no lobby called {msg[lobby_key]}")

            await self.send(json.dumps(
                {
                    type_key: message_key,
                    message_key: F"Die Lobby {msg[lobby_key]} existiert nicht",
                }
            ))

            # close connection with client
            await self.close()

    async def message(self, msg):

        print(F"{msg[message_key][message_key]} was sent by {msg[message_key][channel_key]}")

    async def validate(self, msg):
        '''
        Die Interaktionen des Spielers werden übertragen
        '''
        
        if not self.username:
            #print(F"User {self.username}: Attempting to join game")
            return

        if abs(msg[mouseDelta_key]) > MAX_DEGREE:
            msg[mouseDelta_key] = MAX_DEGREE
            #print("Mouse change invalid!")

        # If both directions are pressed then dont move in those directions
        msg["y"] = msg[up_key] - msg[down_key]

        msg["x"] = msg[right_key] - msg[left_key]


        await self.channelLayer.send(
            "game_engine",
            { 
              "type"    : "validate.event", 
              player_key  : self.username, 
              message_key     : {
                  mouseDelta_key : msg[mouseDelta_key],
                  click_key : msg[click_key],
                  "y" : msg["y"],
                  "x" : msg["x"],
                  weapon_key : msg[weapon_key],
              },
            }
        )
 
    async def game_update(self, event):
        '''
        Send game data to room group after a Tick is processed
        '''

        # Send message to WebSocket
        event = event[state_key] #state
 
        event[type_key] = update_key   #type update

        try:
            # look if the the own username is in the inactive array
            event = event[inactive_key][self.username]
        except KeyError:

            try:
                # drop the information about inactive players
                event.pop(inactive_key)
            except KeyError:
                pass
            # if the map was already sent 10 times
            if(self.map > 10):
                try:
                    event.pop(map_key)
                except KeyError:
                    pass       
            # if the map was not sent that much yet
            else:
                self.map += 1
                pass

        # send the update information to the client
        await self.send(json.dumps(event))

    async def win(self, event):
        '''
        Check if current player won the game and forward the message to player
        '''
        event[type_key] = loose_key #type loose

        for player in event[player_key]: #player

            if player[name_key] == self.username:  #player's name

                event[type_key] = win_key

        await self.send(json.dumps(event))



class GameConsumer(SyncConsumer): 
    '''
    Class, which can communicate is the game engine channel, specifically it runs the infinite game loop ENGINE of one game
    They communicate through channels.
    '''

    def __init__(self):
        """
        Created on demand when the first player joins.
        """
        super().__init__()

        self.channelLayer = get_channel_layer()
        self.engines : dict[GameEngine] = {} #The games are saved in there
        self.lobbies = {} #What player is in what game

    def new_player(self, event):
        '''
        Join an existing game or Create a new game
        '''

        lobbyName : str = event[lobby_key]
        userName  : str = event[player_key]
        channelName : str = event[channel_key]

        lobby : Lobby = Lobby.objects.get(name=lobbyName)

        try:
            # if the game exists he is trying to join and is on the forbidden list
            if(userName in self.engines[lobbyName].playerForbidden):
                print(F"Player {userName} is forbidden to join the game {lobbyName}")
                
                print(channelName)

                async_to_sync(self.channelLayer.send)(
                    channelName, 
                    {
                    "type"   : "message",
                    message_key: F"Player {userName} is forbidden to join the game {lobbyName} because he already joined the game before. It would be cheatin", 
                    }
                )
                return
        except KeyError:
            pass

        # is player already in a game?
        try:
            print(F"Player {userName} already in a game {self.lobbies[userName]}")

            # if the game he is trying to join his current game
            if(self.lobbies[userName] == lobbyName):

                if(len([player for player in self.engines[lobbyName].playerQueue if userName == player.name]) != 0):
                    #rejoin the game
                    self.engines[lobbyName].join_game(userName)
                    
                    print("Player is rejoining the game")

                elif(len([player for player in self.engines[lobbyName].playerQueue if userName == player.name]) != 0):

                    print("Player is trying joining the game even though he is already in")
                
                return

            # if the game is some different game, so that player is going to log out from his old game
            else:
                # if the game exists he wants to join then replace the current status 
                self.replace_lobby(userName, lobbyName, lobby)

        # if he is not already in a game
        except KeyError:
            # for further information in what game the player is
            self.lobbies[userName] = lobbyName 
            lobby.current_players += 1
            lobby.save()

        # look if Lobby is new
        try:
            self.engines[lobbyName].join_game(userName)

        # if the game does not exist, create it
        except KeyError:
            self.new_lobby(lobby, userName)

    def new_lobby(self, lobby, userName):
        '''
        Create new Lobby internally
        '''

        self.engines[lobby.name] = GameEngine(
            lobby.name, 
            maxPlayers=lobby.max_players,
            gameMode=lobby.mode,
            endTime=lobby.game_runtime * 1/TICK_RATE * 60,
            )
        self.engines[lobby.name].start()
        self.engines[lobby.name].join_game(userName)

        #TODO: Only for TESTING
        self.engines[lobby.name].startFlag = True

    def validate_event(self, event):

        username = event[player_key]

        '''
        Send the data to engine
        '''
        try:
            self.engines[self.lobbies[username]].apply_events(username, event[message_key])
        except:
            print(self.lobbies)

    def win(self, event):
        '''
        handling when game is finished
        '''
        lobbyName = event[group_key] #group

        # Synchronize the channel's information and send them to all participants
        async_to_sync(self.channelLayer.group_send)(
            lobbyName, 
            {
             "type"   : "win",
             time_key : event[time_key], #time
             player_key: event[player_key], #player
            }
        )

        # Delete the lobby from the DataBase
        self.delete_lobby(lobbyName)

    def close_game(self, event):
        '''
        When lobby is closed due to inactivity
        '''

        lobbyName = event[group_key] #group

        print(F"Lobby {lobbyName} is closed due to inactivity")
       
        # Delete the lobby from the DataBase
        self.delete_lobby(lobbyName)

    def delete_lobby(self, lobbyName : str) -> None:
        '''
        Delete Lobby in DataBase, Stop the game, set all User free
        '''
        print(F"Lobby {lobbyName} has been deleted")

        Lobby.objects.get(name=lobbyName).delete()

        # Stop the thread by ending its tasks
        #self.engines[groupName].running = False
        self.engines.pop(lobbyName).running = False

        # remove all player from the lobby list
        self.lobbies = {key:lob for key, lob in self.lobbies.items() if lob != lobbyName}
        
    def replace_lobby(self, userName : str, lobbyName : str, lobby : Lobby) -> None:
        '''
        Remove the player from current game and put him there on a forbidden list
        Add the player to a new game
        '''

        print(F"Player {userName} is moving from {self.lobbies[userName]} to {lobbyName}")


        # Remove the Player from former game
        currLobby : Lobby = Lobby.objects.get(name=self.lobbies[userName])
        currLobby.current_players -= 1
        currLobby.save()

        # Add the player to the forbidden list of the game he left
        self.engines[self.lobbies[userName]].playerForbidden.append(userName)

        # Add Player to current game
        self.lobbies[userName] = lobbyName 
        lobby.current_players += 1
        lobby.save()
