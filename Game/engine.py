import logging
import random
import threading
import time
import uuid
import numpy as np
from collections import OrderedDict, deque
from enum import Enum, unique
from typing import Any, Mapping, Optional, Set, Tuple

import math
import copy
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

log = logging.getLogger(__name__)

#TODO: fit that for customized fps
tick_rate = 1

MAPS = [
    [
    "################",
    "#..............#",
    "#........#######",
    "#..............#",
    "#..............#",
    "#.....##.......#",
    "#.....##.......#",
    "#..............#",
    "#..............#",
    "#..............#",
    "######.........#",
    "#....#.........#",
    "#....#.........#",
    "#............###",
    "#............###",
    "################"
    ]
]

#Class for handling coordinates
class Coordinate:
    
    def __init__(self, x : float, y : float):
        
        self.x = x
        self.y = y

    def move(self, speed : float, direction : int):
        # If direction is   0° then the object only moves on y axis in positive direction
        # If direction is  90° then the object only moves on x axis in positive direction
        # If direction is 180° then the object only moves on y axis in negative direction
        # If direction is 270° then the object only moves on x axis in negative direction
        self.x += speed * np.sin(math.radians(direction))

        #print(F"tmp: x_direction: {speed * np.sin(math.radians(direction))}")
        #print(F"tmp: y_direction: {speed * np.cos(math.radians(direction))}")

        self.y += speed * np.cos(math.radians(direction))

    def get_distance(self, sec_cod):

        return math.sqrt((self.x - sec_cod.x) ** 2 + (self.y - sec_cod.y) ** 2)


class Weapon:

    def __init__(self, name : str, max_ammunition : int):
        self.name = name
        self.max_ammunition = max_ammunition
        self.curr_ammunition = max_ammunition

# List for all available weapons
AVAILABLE_WEAPONS = {
    "P99" : Weapon(
        "P99",
        50
    )
}

# Class for handling players
class Player:

    # Initiate player
    def __init__(self, username : str, spawn_x : float = 3, spawn_y : float = 3, direction : float = 0, weapons: list[Weapon] = [AVAILABLE_WEAPONS["P99"]]):
        
        # Initiate the Username
        self.username = username

        # Initiate the current position
        self.current_position = Coordinate(spawn_x + 0.5, spawn_y + 0.5)

        # Represents the health
        self.health = 100

        # Represents the angle, in which the player is facing in degrees
        self.direction = direction

        # Counts down from a specific number to zero for every tick, when it got activated
        self.justShot = 0

        # Counts down from a specific number to zero for every tick, when it got activated
        self.justHit = 0

        self.current_weapon = 0

        # Represents the current available weapons
        self.weapons = weapons

        self.speed = 1

        self.alive = True

    def shoot(self, state):
        '''
        Describes the function to be called when the player shoots
        '''
        
        print(F"{self.username} just shot a bullet!")

        speed = 0.5/tick_rate

        # The animation of shooting shall go on for 1 seconds
        self.justShot = 1/tick_rate

        # Reduce the current ammo of current weapon by one
        self.weapons[self.current_weapon].curr_ammunition -= 1

        dir = math.radians(self.direction)

        # Add bullet to current state
        state.bullets.append(
            Bullet(
                # From whom was a bullet shot?
                self,
                Coordinate(
                    #0.5 Blöcke vom Spieler entfernt entstehen die Bullets
                    self.current_position.x + speed * np.sin(dir),
                    self.current_position.y + speed * np.cos(dir)
                ),
                #Shot in direction of player itself
                self.direction
            )
        )
    
    #Describes the function to be called when the player is hit
    def get_hit(self, player):

        # The animation of getting shot shall go on for 1 second
        self.justShot = 1/tick_rate

        print("Player %s is hit by player %s",self.name, player.name)
        if(self.health > 20):
            self.health -= 20
        else:
            self.health = 0
            #TODO: Was soll nach dem Sterben passieren?

    #Describes the function to be called when the player moves
    def move(self, state, x : int = 0, y: int = 0):

        too_close = False

        # Copy the direction of the player, so that it can be manipulated
        dir = self.direction

        dir += math.degrees(math.atan2(x, y))

        tmp = Coordinate(self.current_position.x, self.current_position.y)

        #print(F"Current position: x: {self.current_position.x}, y: {self.current_position.y}")

        #print("current direction: " + str(self.direction))
        #print("\nrad: " + str(math.atan2(x, y)))
        #print("deg: " + str(math.degrees(math.atan2(x, y))) + "\n")

        #Move only in direction of max math.pi
        tmp.move(self.speed, dir % 360)

        #print(F"Current position: x: {self.current_position.x}, y: {self.current_position.y}")
        #print(F"Tmp position: x: {tmp.x}, y: {tmp.y}")

        # Look for collision with other Players
        for player in state.players:

            # if the on-going move is too close to another player then turn the boolean flag
            if(player.username != self.username and tmp.get_distance(player.current_position) < 1):
                
                #print("Player %s is too close to another player %s", self.name, player.name)
                too_close = True

        if(state.map.check_collision(tmp)):

            print("Player %s is too close to the wall of the map")
            too_close = True

        # if no player is too close to an object
        if(not too_close):
            print (str(tmp.x) + ", " + str(tmp.y))
            self.current_position = tmp

    '''
        Change the direction of the player by the given direction
    '''
    def change_direction(self, mouseX):

        self.direction = (self.direction + mouseX) % 360

        print(F"current direction: {self.direction}")

    def die(self):
        #What should happen?
        #print("Die!")

        # Change the status of the player's condition
        self.alive = False

    def render(self) -> Mapping[str, Any]:
        return{
            "x"         : self.current_position.x,
            "y"         : self.current_position.y,
            "h"         : self.health,
            "dir"       : self.direction,
            "shot"      : self.justShot,
            "hit"       : self.justHit,
            "ammo"      : self.weapons[self.current_weapon].curr_ammunition   
        }



# Class for handling bullets
class Bullet:

    # Initiate bullet
    def __init__(self, origin_player : Player, origin_pos : Coordinate, direction : float):

        print("A bullet has been created")

        self.player           = origin_player
        self.origin_pos       = origin_pos
        self.current_position = origin_pos

        self.direction = direction

        # One Movement per frame
        self.speed = 1

    # Execute for every bullet this function
    def update_pos(self):

        self.current_position.move(self.speed, self.direction)

    # If information is requested for rendering and update the game
    def render(self) -> Mapping[str, Any]:
        return {
            "x": self.current_position.x,
            "y": self.current_position.y
        }


# Class for handling map
class Map:

    def __init__(self, width : int, height : int, map_list : list):
        self.width = width
        self.height = height
        self.map_string = map_list
        self.tick = 0
    
    # validate the input string of map
    # Static Method
    def from_list(strings: list):
        
        for string in strings:
            
            if len(string.replace('#','').replace('.','')) != 0:
                print('Map contains invalid values. It only accepts \"#\" or \".\"')

            #Check if Map fits the format
            if len(string) != len(strings[-1]):
                print("Map is invalid")

        return Map(
            len(string),
            len(strings),
            strings
        )

    # Check if Object collides with Map
    def check_collision(self, coordinate : Coordinate) -> bool:        
        
        #print(self.map_string)

        #print(F"\ny : {int(coordinate.y)}\nx : {int(coordinate.x)}\n")

        #coordinate.derf

        # check collision in for fields around the object
        try:
            if(
                self.map_string[int(coordinate.y)    ][int(coordinate.x)    ] == "#" or
                self.map_string[int(coordinate.y)    ][int(coordinate.x) + 1] == "#" or
                self.map_string[int(coordinate.y) + 1][int(coordinate.x)    ] == "#" or
                self.map_string[int(coordinate.y) + 1][int(coordinate.x) + 1] == "#"
            ):
                return True
            else:
                return False
        except IndexError:
            return True  
        
        
    
    def render(self) -> Mapping[str, Any]:
        return self.map_string

class State:
    '''
    Class for handling the states of the game
    '''

    def __init__(self, map : Map, players : list[Player] = [], bullets : list[Bullet] = []):
        self.map     : Map          = map
        self.players : list[Player] = players
        self.bullets : list[Bullet] = bullets

        #print(self.bullets)

    def render(self) -> Mapping[str, Any]:
        return { 
            "map" :     self.map.render(),
            "players" : {p.username: p.render() for p in self.players},
            "bullets" : [b.render() for b in self.bullets]
        }

# Create a thread to run it indefinitely
class GameEngine(threading.Thread):

    # Constructor function for GameEngine
    def __init__(self, group_name, players_name : list[str] = [], map_string = MAPS[0], **kwargs):
        
        print(F"Initializing GameEngine: {group_name} with players: {players_name}")

        # Create a thread to run the game
        super(GameEngine, self).__init__(daemon = True, name = "GameEngine", **kwargs)

        self.tick_num = 0
        self.name = uuid.uuid4()
        self.group_name = group_name
        self.channel_layer = get_channel_layer()
        self.event_changes = {}
        self.event_lock = threading.Lock()
        self.player_lock = threading.Lock()
        self.player_queue = []

        map_string = MAPS[0]

        self.state = State(
            Map.from_list(map_string), 
            [Player(name) for name in players_name]
            )

    # The main loop for the game engine
    def run(self) -> None:

        #print("Starting engine loop")
        # infinite loop
        while True:

            # After each tick update the current status of the game
            self.state = self.tick()

            # Broadcast the current Status to all players in game
            self.broadcast_state(self.state)

            # Sleep for a specific time, in which the game will calculate every new status
            time.sleep(tick_rate)

    def broadcast_state(self, state: State) -> None: 
        '''
        The broadcast method which broadcast the current game state to the channel
        '''
        
        #print("Broadcasting state to all players in game")

        # Get the current information about the game state
        state_json = state.render()

        # Synchronize the channel's information and send them to all participants
        async_to_sync(self.channel_layer.group_send)(
            self.group_name, 
            {
             "type": "game.update",
             "state": state_json
            }
        )

    def tick(self):
        ''' 
        Function in which every tick it describes

        '''

        self.tick_num += 1
        
        #print(F"Tick {self.tick_num} for game {self.name}")
        
        state = self.state

        with self.event_lock:
            events = self.event_changes.copy()
            self.event_changes.clear()

        if state.players:
            state = self.process_players(state, events)

        if state.bullets:
            state = self.process_bullets(state)
        
        state = self.process_hits(state)
        
        state = self.process_new_players(state)

        state.map.tick = self.tick_num

        return state

    def process_players(self, state: State, events) -> State:

        #print(F"Proccessing players for game {events}")

        for player in state.players:
            
            if player.username in events.keys():
                
                event = events[player.username]

                #print(F"x: {event['x']}, y: {event['y']}")

                player.change_direction(event["mouseDeltaX"])

                if(event["x"] != 0 or event["y"] != 0):
                    player.move(state, event["x"], event["y"])

                if(event["leftClick"]):
                   player.shoot(state)
        
        return state
            
    def process_hits(self, state: State) -> State:

        #print(F"Proccessing collisions for game {self.name}")

        for player in state.players:

            got_hit = False

            for bullet in state.bullets: 

                # If the bullet is too close to the player, then recognize it as a collision
                if bullet.current_position.get_distance(player.current_position) < 0.1:

                    got_hit = True
                    break

            # if the player got hit change the state of the player
            if got_hit: 

                player.get_hit(bullet.player)

        return state

    def process_bullets(self, state: State) -> State:

        print(F"Proccessing bullets {state.bullets}")

        for bullet in state.bullets:

            # Make the next move for all bullets
            bullet.update_pos()

        return state

    def apply_events(self, player: str, events) -> None:
        '''
        Transfer the changes from the GameConsumer to the GameEngine
        '''

        #print("Applying changes for " + player)
        
        with self.event_lock:
            self.event_changes[player] = events

    def join_game(self, player: str) -> None:

        #print(F"Player {player} joined game!", )

        if player in self.state.players:

            #print(F"Player {player} is already in game!")
            return
        
        with self.player_lock:

            self.player_queue.append(Player(player, 3, 3))

    def process_new_players(self, state: State):

        #print(F"Processing new players for game: {self.name}")

        # add the players to the game
        state.players += self.player_queue

        # Clear the queue
        self.player_queue = []

        return state

        



