
import logging
import json

from asgiref.sync               import  async_to_sync
from channels.consumer          import SyncConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers            import get_channel_layer
from lobby.models               import Lobby
from channels.db                import database_sync_to_async

from .engine import GameEngine, TICK_RATE, MAX_DEGREE



log = logging.getLogger(__name__)

#Key Constants
channel_key    = 'c'
click_key      = 'c'
down_key       = 'd'
group_key      = 'g'
inactive_key   = 'i'
init_key       = 'y'
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
    """Async Consumer which gets the data from the client synchronously, but in perspective of the worker GameConsumer asynchronously.
        It sends then the data to GameConsumer

    Inherits:
         AsyncWebsocketConsumer: The AsyncWebsocketConsumer is a asynchronous websocket
    """

    @database_sync_to_async
    def get_lobby(self, lobbyName) -> Lobby | None:
        """Is an asynchronous function to get lobby information about the recieved lobbyname. If there is no lobby called like 'lobbyname', an exception is raised

        Args:
            lobbyName (str): name of the lobby

        Returns:
            Lobby: information about lobby
        """

        return Lobby.objects.filter(name=lobbyName).first()
        #return Lobby.objects.get(name=lobbyName)

    @database_sync_to_async
    def get_last_lobby(self) -> list[Lobby]:
        """Get last lobby in the database for testing

        Returns:
            list(Lobby): Contains all active lobbies
        """
        lobby : Lobby = list(Lobby.objects.all().values())

        return lobby
 
    async def connect(self) -> None:
        """Function is called by the client if he tries to connect to the PlayerConsumer
           The username of the logged in user will be assigned to the PlayerConsumer
        """
        #If user is unknown
        if self.scope["user"].is_anonymous:
            print("User is unknown. So he has been disconnected")
            await self.close()
        
        self.username = self.scope["user"].user_name

        # Accept the connection with Browser
        await self.accept()

    async def disconnect(self, close_code) -> None:
        """Disconnect the consumer from the client if he leaves the game or the game ends

        Args:
            close_code (str): the code
        """

        try:
            print(F"Disconnect: {close_code}")
            await self.channelLayer.group_discard(
                self.groupName,
                self.channel_name
            )
        except:
            pass
    
    async def receive(self, text_data=None, byte_data=None) -> None:
        """This the function which automatically recieves the data from the client, when the client send data to websocket. It forwards the data to the specific 
           functions:
                validate(msg)
                join_lobby(msg)

        Args:
            text_data (JSON, optional): In json wrapped data. Defaults to None.
            byte_data (Bytes, optional): data in bytes. Defaults to None.

        Returns:
            None:
        """

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

    async def join_lobby(self, msg) -> None:
        """Called by recieve function. It checks if the lobby is open and joinable.
                If not then the client will be disconnected from the consumer.
                If yes then the worker GameEngine will be called to distribute the player on the correct game

        Args:
            msg (dict): contains the user information and the lobby name
        """

        #if there is a lobby
        lobby = await self.get_lobby(msg[lobby_key])

        if(lobby):
            print(F"Join lobby {lobby.name}")

            try:
                self.scope["lobby"]
            except:
                print("Set default value")
                #Default value
                self.scope["lobby"] = ""

            # If the max player was reached and the player is not currently in the game
            if(lobby.current_players >= lobby.max_players and not lobby.name in self.scope["lobby"]):
                
                await self.send(json.dumps(
                    {
                        type_key: message_key,
                        message_key: F"Die Lobby {msg[lobby_key]} ist bereits voll",
                    }
                ))
                
                print(F"Too many players in Lobby {lobby.name}")
                await self.close()
            else:
                self.channelLayer = get_channel_layer()
                self.groupName = msg[lobby_key]

                # Has init already been sent?
                self.init = 0

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
        else:
            print(F"There is no lobby called >>{msg[lobby_key]}<<. Last is >>{await self.get_last_lobby()}<<")

            await self.send(json.dumps(
                {
                    type_key: message_key,
                    message_key: F"Die Lobby {msg[lobby_key]} existiert nicht",
                }
            ))

            # close connection with client
            await self.close()

    async def message(self, msg) -> None:
        """Handles messages if they should be printed by PlayerConsumer

        Args:
            msg (dict): contains the message
        """

        print(F"{msg[message_key][message_key]} was sent by {msg[message_key][channel_key]}")

    async def validate(self, msg) -> None:
        """ Called by recieve and gets the input of the client
            Here is already checked if mouse input is valid and transform the movement in shorter expression
            Forwards the input to the GameConsumer for distribution to lobby

        Args:
            msg (dict): contains the input
        """
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
 
    async def game_update(self, event) -> None:
        """ Called by the GameConsumer when new information is ready to distribute to the client
            Deletes the init information in content if already sent
            Deletes the information about player if not permitted to see

        Args:
            event (dict): contains the updated information
        """

        # Send message to WebSocket
        event = event[state_key]
 
        event[type_key] = update_key

        try:
            # look if the the own username is in the inactive array
            event = event[inactive_key][self.username]
        except KeyError:

            try:
                # drop the information about inactive players
                event.pop(inactive_key)
            except KeyError:
                pass
            # if the init was already sent 10 times
            if(self.init > 10):
                try:
                    event.pop(init_key)
                except KeyError:
                    print("There is no init_key")
                    pass       
            # if the init was not sent that much yet
            else:
                self.init += 1
                pass

        # send the update information to the client
        await self.send(json.dumps(event))

    async def win(self, event) -> None:
        """Check if current player won the game and forward the message to player
            If the player is not part of the winning player then send lose

        Args:
            event (dict): contains the information about the winning player
        """
        '''
        
        '''
        event[type_key] = loose_key #type loose

        for player in event[player_key]: #player

            if player[name_key] == self.username:  #player's name

                event[type_key] = win_key

        await self.send(json.dumps(event))

class GameConsumer(SyncConsumer): 
    """Class, which can communicate is the game engine channel, specifically it runs the infinite game loop ENGINE of one game
    They communicate through channels.

    Inherits:
         SyncConsumer: Is a consumer/worker which handles all lobbies and players
    """

    def __init__        (self):
        """
        Constructor, which is called when first player wants to join the first game
        """

        super().__init__()

        # gets all current channels
        self.channelLayer = get_channel_layer()

        # Every game/lobby is saved in here
        self.engines : dict[GameEngine] = {} 

        # Saves the player's information about his lobby
        self.lobbies = {}

    def new_player      (self, event : dict)                    -> None:
        """ Called by the asynchronous PlayerConsumer
            Join an existing game or create a new game. If player is already in a lobby then either forbidden to join, change lobby or rejoin

        Args:
            event (dict): contains information about the user and the lobby he wants to join
        """

        lobbyName : str = event[lobby_key]
        userName  : str = event[player_key]
        channelName : str = event[channel_key]

        lobby : Lobby = Lobby.objects.filter(name=lobbyName).first()

        try:
            # if the game exists he is trying to join and is on the forbidden list
            if(userName in self.engines[lobbyName].playerForbidden):
                print(F"Player {userName} is forbidden to join the game {lobbyName}")

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
                    #TODO: Testen
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

    def new_lobby       (self, lobby : Lobby, userName : str)   -> None:
        """Called by new_player function if new lobby should be created. Create the lobby with the settings of the database

        Args:
            lobby (Lobby): Lobby object from database
            userName (str): the username
        """

        self.engines[lobby.name] = GameEngine(
            lobby.name, 
            lobby.map,
            maxPlayers          = lobby.max_players,
            gameMode            = lobby.mode,
            endTime             = lobby.game_runtime * 1/TICK_RATE * 60,
            )
        self.engines[lobby.name].start()
        self.engines[lobby.name].join_game(userName)

        #TODO: Only for TESTING
        self.engines[lobby.name].startFlag = True

    def validate_event  (self, event : dict)                    -> None:
        """Called by asynchronous PlayerConsumer to get input and distribute on the lobby

        Args:
            event (dict): the input from the PlayerConsumer
        """

        username = event[player_key]

        '''
        Send the data to engine
        '''
        try:
            self.engines[self.lobbies[username]].apply_events(username, event[message_key])
        except:
            print(self.lobbies)

    def win             (self, event : dict)                    -> None:
        """Called by the lobby and send to every player in the lobby that the game is finished. It sends the information about the winning players

        Args:
            event (dict): contains the winning players
        """

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

    def close_game      (self, event : dict)                    -> None:
        """Closes a specific lobby if no player is active anymore

        Args:
            event (dict): contains the name of the lobby to close
        """

        lobbyName = event[group_key]

        print(F"Lobby {lobbyName} is closed due to inactivity")
       
        # Delete the lobby from the DataBase
        self.delete_lobby(lobbyName)

    def delete_lobby    (self, lobbyName : str)                 -> None:
        """Deletes a lobby

        Args:
            lobbyName (str): lobby name
        """
        
        print(F"Lobby {lobbyName} has been deleted")

        # Find and delete the lobby
        Lobby.objects.filter(name=lobbyName).first().delete()

        # Stop the thread by ending its tasks
        #self.engines[groupName].running = False
        self.engines[lobbyName].startFlag = False
        self.engines.pop(lobbyName).stopFlag = True

        # remove all player from the lobby list
        self.lobbies = {key:lob for key, lob in self.lobbies.items() if lob != lobbyName}
        
    def replace_lobby   (self, userName : str, lobby : Lobby)   -> None:
        """
        Remove the player from current game and put him there on a forbidden list
        Add the player to a new game

        Args:
            userName (str): Name of the user
            lobby (Lobby): Lobby object of the one he wants to join
        """

        print(F"Player {userName} is moving from {self.lobbies[userName]} to {lobby.name}")


        # Remove the Player from former game
        #currLobby : Lobby = Lobby.objects.get(name=self.lobbies[userName])
        currLobby : Lobby = Lobby.objects.filter(name=self.lobbies[userName]).first()
        currLobby.current_players -= 1
        currLobby.save()

        # Add the player to the forbidden list of the game he left
        self.engines[self.lobbies[userName]].playerForbidden.append(userName)

        # Add Player to current game
        self.lobbies[userName] = lobby.name
        lobby.current_players += 1
        lobby.save()
