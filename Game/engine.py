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
from pyparsing import col

log = logging.getLogger(__name__)

#TODO: fit that for customized fps
tick_rate = 0.01

#Reversed direction
MAPS = [
    [
    "################",
    "#............W.#",
    "#........#######",
    "#............N.#",
    "#..............#",
    "#.....##.......#",
    "#.....##.......#",
    "#..............#",
    "#.E............#",
    "#..............#",
    "######.........#",
    "#....#.........#",
    "#.N..#.........#",
    "#..........S.###",
    "#............###",
    "################"
    ]
]

#Class for handling coordinates
class Coordinate:
    
    def __init__(self, x : float, y : float):
        
        self.x = x
        self.y = y

    def cod_move(self, speed : float = 0, dir : float = 0):

        # If direction is   0° then the object only moves on y axis in positive direction
        # If direction is  90° then the object only moves on x axis in positive direction
        # If direction is 180° then the object only moves on y axis in negative direction
        # If direction is 270° then the object only moves on x axis in negative direction
        self.x += speed * np.sin(dir)
        self.y += speed * np.cos(dir)

    def get_distance(self, sec_cod):

        return math.sqrt((self.x - sec_cod.x) ** 2 + (self.y - sec_cod.y) ** 2)

class Spawn:

    def __init__(self, coordinate : Coordinate = Coordinate(3.5,3.5), direction : float = 0):

        self.coordinate = coordinate

        self.direction = direction

        self.player = None

        self.lock_time = 0

    def use(self, player):

        self.player = player

        # The Spawn is occupied for 5 Seconds
        self.lock_time = 5/tick_rate

    def update(self):

        if(self.lock_time == 0):
            self.player = None
        else:
            self.lock_time -= 1

class Weapon:

    def __init__(self, name : str, max_ammunition : int, latency : int):
        self.name = name
        self.max_ammunition = max_ammunition
        self.curr_ammunition = max_ammunition
        self.latency = latency
        self.curr_latency = 0

# List for all available weapons
AVAILABLE_WEAPONS = {
    "P99" : Weapon(
        "P99",
        50,
        0.2/tick_rate,
    ),
    "MP5" : Weapon(
        "MP5",
        200,
        1/tick_rate,        
    ),
}

class Map:
    '''
    Class for handling the map
    It can read a map from strings array
    '''

    def __init__(self, width : int, height : int, map_list : list, spawns : list[Spawn]):
        self.width = width
        self.height = height
        self.map_string = map_list
        self.spawns = spawns
        self.tick = 0
    
    # validate the input string of map
    # Static Method
    def from_list(strings: list):

        spawns = list()
        
        for idx_s, string in enumerate(strings):
            
            if len(string.replace('#','').replace('.','').replace('N','').replace('E','').replace('S','').replace('W','')) != 0:
                print('Map contains invalid values. It only accepts \"#\" or \".\" and spawn fields')

                        #Check if Map fits the format
            if len(string) != len(strings[-1]):
                print("Map is invalid")

            #Handling for spawns
            for idx_c, char in enumerate(string):

                #Check if the direction fits to the coordinate
                if(char == 'N' and strings[idx_s-1][idx_c] == '.'):
                    spawns.append(
                        Spawn(
                            Coordinate(
                            idx_c + 0.5,
                            idx_s + 0.5,
                            ),
                            0,
                        )
                    )

                #Check if the direction fits to the coordinate
                if(char == 'E' and strings[idx_s][idx_c+1] == '.'):
                    spawns.append(
                        Spawn(
                            Coordinate(
                            idx_c + 0.5,
                            idx_s + 0.5,
                            ),
                            math.pi/2,
                        )
                    )
            
                #Check if the direction fits to the coordinate
                if(char == 'S' and strings[idx_s+1][idx_c] == '.'):
                    spawns.append(
                        Spawn(
                            Coordinate(
                            idx_c + 0.5,
                            idx_s + 0.5,
                            ),
                            math.pi,
                        )
                    )
            
                #Check if the direction fits to the coordinate
                if(char == 'W' and strings[idx_s][idx_c-1] == '.'):
                    spawns.append(
                        Spawn(
                            Coordinate(
                            idx_c + 0.5,
                            idx_s + 0.5,
                            ),
                            -math.pi/2,
                        )
                    )
            
        if(len(spawns) == 0):
            print("Map contains no spawn fields")

        return Map(
            len(string),
            len(strings),
            strings,
            spawns,
        )

    # Check if Object collides with Map
    # Returns True if Oject collide with wall in any way
    def check_collision(self, coordinate : Coordinate, object) -> int:        

        # check collision in for fields around the object
        collision = False

        try:
            A = self.map_string[round(coordinate.y - 0.8)][round(coordinate.x - 0.8)] == "#"
            B = self.map_string[round(coordinate.y - 0.8)][round(coordinate.x - 0.3)] == "#"
            C = self.map_string[round(coordinate.y - 0.3)][round(coordinate.x - 0.8)] == "#"
            D = self.map_string[round(coordinate.y - 0.3)][round(coordinate.x - 0.3)] == "#"

            A_l = self.map_string[round(coordinate.y - 0.57)][round(coordinate.x - 0.57)] == "#"
            B_l = self.map_string[round(coordinate.y - 0.57)][round(coordinate.x - 0.43)] == "#"
            C_l = self.map_string[round(coordinate.y - 0.43)][round(coordinate.x - 0.57)] == "#"
            D_l = self.map_string[round(coordinate.y - 0.43)][round(coordinate.x - 0.43)] == "#"
            Corner = self.map_string[round(coordinate.y - 0.5)][round(coordinate.x - 0.5)] == "#"

            '''
            print(F"A_l: {A_l}")
            print(F"B_l: {B_l}")
            print(F"C_l: {C_l}")
            print(F"D_l: {D_l}")
            print(F"A: {A}")
            print(F"B: {B}")
            print(F"C: {C}")
            print(F"D: {D}")
            print(F"cor: {Corner}\n\n")
            '''

            north = A and B
            east = B and D
            south = C and D
            west = A and C

            ne = A and B and D  or     A_l and not B_l and not C_l and not D_l
            se = B and C and D  or not A_l and     B_l and not C_l and not D_l
            sw = A and C and D  or not A_l and not B_l and     C_l and not D_l
            nw = A and B and C  or not A_l and not B_l and not C_l and     D_l     

            # If Player is in corner, dont change anything
            if ne or se or sw or nw:
                #print(F"Player is located at a corner: y: {coordinate.y} x: {coordinate.x}")
                return True

            # if Player is not located at east nor west wall
            if not (west or east):
                object.current_position.x = coordinate.x
            else:
                collision = True
            
        
            # if Player is not located at north nor south wall
            if not (north or south):
                object.current_position.y = coordinate.y
            else:
                collision = True
            
            return collision

        except IndexError:
            print("Bewegung war ungültig und wurde zurückgesetzt!")
            object.current_position = Coordinate(3.5,3.5)
            return True
        
    def render(self) -> Mapping[str, Any]:
        return self.map_string

class Player:
    '''
    Class for handling players
    '''


    # Initiate player
    def __init__(self, username : str, map : Map, weapons: list[Weapon] = [AVAILABLE_WEAPONS["P99"]], speed : float = tick_rate/0.1, rotation_speed : float = tick_rate/1,):
        
        # Initiate the Username
        self.name = username

        # While no the right the spawn is found
        while True:

            print("Find spawn")

            self.spawn = random.choice(map.spawns)

            # if the spawn is not yet occupied
            if(self.spawn.player is None):
                break

        print(F"\nSpawn: x: {self.spawn.coordinate.x} y: {self.spawn.coordinate.y}")

        #Declare the Spawn as used
        self.spawn.use(self)

        # Initiate the current position
        self.current_position = self.spawn.coordinate

        # Represents the health
        self.health = 100

        # Represents the angle, in which the player is facing in radians
        self.direction = self.spawn.direction

        # Counts down from a specific number to zero for every tick, when it got activated
        self.justShot = 0

        # Counts down from a specific number to zero for every tick, when it got activated
        self.justHit = 0

        self.current_weapon = 0

        # Represents the current available weapons
        self.weapons = weapons

        '''
        Float describes how fast the Player is moving
        '''
        self.speed = speed

        '''Float describes how fast the Player is rotating'''
        self.rotation_speed = rotation_speed

        '''
        Boolean whether player is alive or died
        '''
        self.alive = True

        '''
        Counts how many times a player did not send something in a row
        '''
        self.delayed_tick = 0

    def shoot(self, state):
        '''
        Describes the function to be called when the player shoots
        '''
        
        weapon = self.weapons[self.current_weapon]

        if weapon.curr_ammunition > 0 and weapon.curr_latency == 0:

            print(F"{self.name} just shot a bullet!")

            speed = 0.5/tick_rate

            # The animation of shooting shall go on for 1 seconds
            self.justShot = 1/tick_rate

            # Reduce the current ammo of current weapon by one
            weapon.curr_ammunition -= 1

            # Start the delay of the weapon
            weapon.curr_latency = weapon.latency

            dir = self.direction

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
        else:

            print(F"{self.name} has no bullets: {weapon.curr_ammunition} or latency is still active : {weapon.curr_latency} ")


    #Describes the function to be called when the player is hit
    def get_hit(self, player):

        # The animation of getting shot shall go on for 1 second
        self.justShot = 1/tick_rate

        print(F"Player {self.name} is hit by player {player.name}")
        if(self.health > 20):
            self.health -= 20
        else:
            self.health = 0
            self.die()

    #Describes the function to be called when the player moves
    def move(self, state, x : int = 0, y: int = 0):

        too_close = False

        # Copy the direction of the players, so that it can be manipulated
        dir = self.direction

        dir += math.atan2(x, y)

        tmp = Coordinate(self.current_position.x, self.current_position.y)

        if dir < 0:
            dir = (dir % -(2*math.pi)) 
            if dir < -math.pi:
                dir = dir % (math.pi + 0.00001)
        else:
            dir = (dir % (2*math.pi))
            if dir > math.pi:
                dir = dir % -(math.pi + 0.00001)

        #Move only in direction of max math.pi
        tmp.cod_move(self.speed, dir)

        # Look for collision with other Players
        for player in state.players:

            # if the on-going move is too close to another player then turn the boolean flag
            if(player.name != self.name and tmp.get_distance(player.current_position) < 1):
                
                print(F"Player {self.name} is too close to another player {player.name}")
                too_close = True

        # if player is not too close to an object
        if(not too_close):
            state.map.check_collision(tmp, player)

        '''
        col = state.map.check_collision(tmp)

        if(col == 3):
            print(F"Player {self.name} is too close to the wall of the map x: {tmp.x} y: {tmp.y}")
            too_close = True
        elif(col == 1):
            tmp.x = self.current_position.x
        elif(col == 2):
            tmp.y = self.current_position.y
        '''

            #self.current_position = tmp

    '''
        Change the direction of the player by the given direction
    '''
    def change_direction(self, mouseX):

        dir = self.direction + mouseX * self.rotation_speed

        if dir < 0:
            dir = (dir % -(2*math.pi)) 
            if dir < -math.pi:
                dir = dir % (math.pi + 0.00001)
        else:
            dir = (dir % (2*math.pi))
            if dir > math.pi:
                dir = dir % -(math.pi + 0.00001)
        
        self.direction = dir

    '''
    Function for Player died
    '''
    def die(self):
        #What should happen?
        print("Die!")

        # Change the status of the player's condition
        self.alive = False

    '''
    Returns all relevant information about the Player for the Client
    '''
    def render(self) -> Mapping[str, Any]:
        return{
            "x"         : self.current_position.x,
            "y"         : self.current_position.y,
            "h"         : self.health,
            "dir"       : self.direction,
            "shot"      : self.justShot,
            "hit"       : self.justHit,
            "ammo"      : self.weapons[self.current_weapon].curr_ammunition,
            "alive"     : self.alive,
        }


class Bullet:
    '''
    Creating and handling Bullets
    '''

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
    # Returns True if bullet collide with Wall or Player
    def update_pos(self, map : Map):

        tmp = Coordinate(self.current_position.x,self.current_position.y)

        tmp.cod_move(self.speed, self.direction)

        # Check collision with Wall
        if map.check_collision(tmp, self):
            return True
        else:
            #if Bullet did not collide with wall
            self.current_position = tmp
            return False


    # If information is requested for rendering and update the game
    def render(self) -> Mapping[str, Any]:
        return {
            "x": self.current_position.x,
            "y": self.current_position.y
        }


class State:
    '''
    Class for handling the states of the game
    '''

    def __init__(self, map : Map, players_name : list[str] = [], bullets : list[Bullet] = []):
        self.map     : Map          = map
        self.players : list[Player] = [Player(name, map) for name in players_name]
        self.bullets : list[Bullet] = bullets


    def render(self) -> Mapping[str, Any]:
        return { 
            "map" :     self.map.render(),
            "players" : {p.name: p.render() for p in self.players},
            "bullets" : [b.render() for b in self.bullets]
        }

# Create a thread to run it indefinitely
class GameEngine(threading.Thread):

    # Constructor function for GameEngine
    def __init__(self, group_name, players_name : list[str] = [], map_string = MAPS[0], max_players : int = 6, **kwargs):
        
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

        #How man players are allowed in the game
        self.max_players = max_players

        map_string = MAPS[0]

        self.state = State(
            Map.from_list(map_string), 
            players_name
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
            
            #if player did not respond for one second or more
            if player.delayed_tick >= 1/tick_rate:

                #TODO: What happens if the User does not respond

                print(F"Player {player.name} did not respond for one second or more! So he was removed!")

                self.state.players.remove(player)

                continue

            if player.name in events.keys():

                
                if(player.delayed_tick > 1):
                    print(F"Player {player.name} did not respond for {player.delayed_tick} ticks")

                #reset the delayed_tick
                player.delayed_tick = 0

                weapon = player.weapons[player.current_weapon]

                if(weapon.curr_latency > 0):
                    # reduce the latency of the current weapon
                    weapon.curr_latency -= 1
                
                event = events[player.name]

                player.change_direction(event["mouseDeltaX"])

                if(event["x"] != 0 or event["y"] != 0):
                    player.move(state, event["x"], event["y"])

                if(event["leftClick"]):
                   player.shoot(state)
            else:
                #Increase the delayed tick of the player
                player.delayed_tick += 1


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

        # Make the next move for all bullets
        # if True then it collide with Wall or Player, so remove it
        state.bullets = [bullet for bullet in state.bullets if not bullet.update_pos(state.map)]

        return state

    def apply_events(self, player: str, events) -> None:
        '''
        Transfer the changes from the GameConsumer to the GameEngine
        '''

        #print("Applying changes for " + player)
        
        with self.event_lock:
            self.event_changes[player] = events

    def join_game(self, player: str) -> None:

        print(F"\n\nPlayer {player} joined game!\n\n", )

        # Look if player is already in the game
        if not next((obj for obj in self.state.players if obj.name == player), None) is None:

            print(F"\n\nPlayer {player} is already in game!\n")
            return
        
        with self.player_lock:
            # Append Player to the queue so it can be appended to the game
            self.player_queue.append(Player(player, self.state.map))

    def process_new_players(self, state: State):

        #print("Process new Players")

        if(len(self.player_queue) != 0):

            # add the players to the game
            state.players += self.player_queue

            # Clear the queue
            self.player_queue = []

        return state

        



