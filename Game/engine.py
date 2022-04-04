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
tick_rate = 0.16

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

@unique
class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

#Class for handling coordinates
class Coordinate:
    
    def __init__(self, x : float, y : float):
        
        self.x_coordinate = x
        self.y_coordinate = y

    def move(self, speed : float, direction : int):
        # If direction is   0° then the object only moves on y axis in positive direction
        # If direction is  90° then the object only moves on x axis in positive direction
        # If direction is 180° then the object only moves on y axis in negative direction
        # If direction is 270° then the object only moves on x axis in negative direction
        return Coordinate(self.x_coordinate + speed * np.sin(direction),
                          self.y_coordinate + speed * np.cos(direction)
        )

    def get_distance(self, sec_cod):

        return math.sqrt((self.x_coordinate - sec_cod.x_coordinate) ** 2 + (self.y_coordinate - sec_cod.y_coordinate) ** 2)


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
    def __init__(self, username : str, spawn_x : float = 0, spawn_y : float = 0, direction : float = 0, weapons: list[Weapon] = [AVAILABLE_WEAPONS["P99"]]):
        
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

        self.speed = 0.01

        self.alive = True

    def render(self) -> Mapping[str, Any]:
        return{
            "x"         : self.current_position.x_coordinate,
            "y"         : self.current_position.x_coordinate,
            "h"         : self.health,
            "dir"       : self.direction,
            "shot"      : self.justShot,
            "hit"       : self.justHit,
            "ammo"      : self.weapons[self.current_weapon].curr_ammunition   
        }

    #Describes the function to be called when the player shoots
    def shoot(self, state):
        
        # The animation of shooting shall go on for 1 seconds
        self.justShot = 1/tick_rate

        # Reduce the current ammo of current weapon by one
        self.weapons[self.current_weapon].curr_ammunition -= 1

        # Add bullet to current state
        state.bullets.append(
            Bullet(
                # From whom was a bullet shot?
                self,
                Coordinate(
                    #0.5 Blöcke vom Spieler entfernt entstehen die Bullets
                    self.current_position.x_coordinate + 0.5 * np.sin(self.direction),
                    self.current_position.y_coordinate + 0.5 * np.cos(self.direction)
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
    def move(self, state, up : bool = False, right : bool = False, down : bool = False, left : bool = False):

        too_close = False

        # Copy the direction of the player, so that it can be manipulated
        dir = self.direction.copy()

        # upper right: 45° == math.pi/4
        if(up and right):
            dir += math.pi/4

        # right: 90° == math.pi/2
        elif(right):
            dir += (math.pi/2)

        # lower right: 125° == math.pi/2 + math.pi/4
        elif(down and right):
            dir += (math.pi/2 + math.pi/4)

        # down: 180° == math.pi
        if(down):
            dir += math.pi

        # down left: 225° == math.pi + math.pi/4
        elif(down and left):
            dir -= (math.pi/2 + math.pi/4)

        # left: 270° == math.pi + math.pi/2
        elif(left):
            dir -= math.pi/2

        # upper left: 315° == math.pi + math.pi/2 + math.pi/4
        elif(up and left):
            dir -= math.pi/4

        tmp = copy.deepcopy(self.current_position)

        #Move only in direction of max math.pi
        tmp.move(self.speed, dir%math.pi)

        # Look for collision
        for player in state.players:

            # if the on-going move is too close to another player then turn the boolean flag
            if(tmp.get_distance(player.current_position) < 1):
                
                print("Player %s is too close to another player %s", self.name, player.name)
                too_close = True

            if(state.map.check_collision(self.tmp)):

                print("Player %s is too close to the wall of the map")
                too_close = True

        # if no player is too close to an object
        if(not too_close):

            self.current_position = tmp


    def change_direction(self, mouseX, mouseY):

        self.direction += mouseX

    def die(self):
        #What should happen?
        print("Die!")

        # Change the status of the player's condition
        self.alive = False


# Class for handling bullets
class Bullet:

    # Initiate bullet
    def __init__(self, origin_player : Player, origin_pos : Coordinate, direction : float):

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
            "x": self.current_position.x_coordinate,
            "y": self.current_position.y_coordinate
        }


# Class for handling map
class Map:

    def __init__(self, width : int, height : int, map_list : list):
        self.width = width
        self.height = height
        self.map_string = map_list
        self.tick = 0
    
    # validate the input string of map
    def from_list(self, strings: list):
        
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
        
        # check collision in for fields around the object
        if(
            self.map_string[int(coordinate.y_coordinate)    ][int(coordinate.x_coordinate)    ] == "#" or
            self.map_string[int(coordinate.y_coordinate)    ][int(coordinate.x_coordinate) + 1] == "#" or
            self.map_string[int(coordinate.y_coordinate) + 1][int(coordinate.x_coordinate)    ] == "#" or
            self.map_string[int(coordinate.y_coordinate) + 1][int(coordinate.x_coordinate) + 1] == "#"
        ):
            return True
        else:
            return False
    
    def render(self) -> Mapping[str, Any]:
        return self.map_string

# Class for handling the states of the game
class State:

    def __init__(self, map : Map, players : list[Player]):
        self.map     : Map          = map
        self.players : list[Player] = players
        self.bullets : list[Bullet] = []

    def render(self) -> Mapping[str, Any]:
        return { 
            "map" :     self.map.render(),
            "players" : {p.username: p.render() for p in self.players},
            "bullets" : [b.render() for b in self.bullets]
        }

# Create a thread to run it indefinitely
class GameEngine(threading.Thread):
    
    INVALID_MOVES = {
        (Direction.UP, Direction.DOWN),
        (Direction.DOWN, Direction.UP),
        (Direction.LEFT, Direction.RIGHT),
        (Direction.RIGHT, Direction.LEFT),
    }

    def __init__(self, group_name, players_name : list[str], map_string = MAPS[0], **kwargs):
        
        print("Initializing GameEngine: %s with players: %s", group_name, players_name)

        # Create a thread to run the game
        super(GameEngine, self).__init__(daemon = True, name = "GameEngine", **kwargs)

        self.tick_num = 0
        self.name = uuid.uuid4()
        self.group_name = group_name
        self.channel_layer = get_channel_layer()
        self.event_changes = {}
        self.event_lock = threading.Lock()
        self.player_lock = threading.Lock()
        self.player_queue = list[Player]

        self.state = State(
            Map.from_list(map_string), 
            [Player(name) for name in players_name]
            )

    # The main loop for the game engine
    def run(self) -> None:

        print("Starting engine loop")

        # infinite loop
        while True:

            # After each tick update the current status of the game
            self.state = self.tick()

            # Broadcast the current Status to all players in game
            self.broadcast_state(self.state)

            # Sleep for a specific time, in which the game will calculate every new status
            time.sleep(self.tick_rate)

    # The broadcast method which broadcast the current game state
    def broadcast_state(self, state: State) -> None: 
        
        # Get the current information about the game state
        state_json = state.render()

        # Get the channel
        channel_layer = get_channel_layer()

        # Synchronize the channel's information and send them to all participants
        async_to_sync(channel_layer.group_send)(
            self.group_name, {"type": "game_update", "state": state_json}
        )

    def tick(self):
        self.tick_num += 1
        print("Tick %d for game %s", self.tick_num, self.name)
        state = self.state

        with self.event_lock:
            events = self.event_changes.copy()
            self.event_changes.clear()

        state = self.process_players(state, events)
        state = self.process_bullets(state)
        state = self.process_collisions(state)
        state = self.process_new_players(state)

        state.map.tick = self.tick_num

        return state

    def process_players(self, state: State, events):
        print("Proccessing players for game %s", self.name)

        for player in state.players:
            
            if player.username in events.keys():
                
                event = events[player.username]

                player.move(event["Up"],event["Right"],event["Down"],event["Left"])

                player.change_direction(event("MouseX"), event["MouseY"])

                if(event["LeftClick"]):
                    player.shoot(state)
            
    def process_collisions(self, state: State):
        print("Proccessing collisions for game %s", self.name)

        for player in state.players:

            got_hit = False

            for bullet in state.bullets: 

                # If the bullet is too close to the player, then recognize it as a collision
                if bullet.current_position.get_distance(player.current_position) < 0.1:

                    got_hit = True
                    break

            if got_hit: 

                player.get_hit(bullet.player)

    def process_bullets(self, state: State):
        
        for bullet in state.bullets:

            bullet.update_pos()

    def apply_events(self, player: str, events):

        print("Applying changes for %s", player)
        with self.event_lock:
            self.event_changes[player] = events

    def join_game(self, player: str) -> None:

        print("Player %s joined game!", player)

        if player in self.state.players:

            print("Player %s is already in game!", player)
            return
        
        with self.player_lock:

            self.player_queue.append(Player(player, 3, 3))

    def process_new_players(self, state: State):

        print("Processing new players for game: %s", self.name)

        state.players += self.player_queue

        return state

        



