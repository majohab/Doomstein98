import logging
from multiprocessing.sharedctypes import Value
from operator import attrgetter
import random
import threading
import time
import uuid
import numpy as np
from typing import Any, Mapping

import math
import pandas as pd
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from copy import deepcopy

log = logging.getLogger(__name__)

#TODO: fit that for customized fps
TICK_RATE = 0.016

PLAYER_SPEED            = TICK_RATE/0.1
ROTATION_SPEED          = TICK_RATE/1
BULLET_SPEED            = TICK_RATE/0.025


# Every Unit is in Seconds
JUST_SHOT_ANIMATION     = round(1/TICK_RATE)   # 1 Second
JUST_HIT_ANIMATION      = round(1/TICK_RATE)   # 1 Second
JUST_DIED_ANIMATION     = round(10/TICK_RATE)

CHANGE_WEAPON_DELAY     = round(1/TICK_RATE)   # 1 Second
SPAWN_LOCK_TIME         = round(10/TICK_RATE)  # 10 Seconds
REVIVE_WAITING_TIME     = round(10/TICK_RATE)  # 10 Seconds
PLAYER_DELAY_TOLERANCE  = round(3/TICK_RATE)
PLAYER_WAITING_TIME_AFTER_NOT_RESPONDING = round(10/TICK_RATE)
PLAYER_WAITING_TIME_OCCUPIED_SPAWN = round(0.1/TICK_RATE)

MAX_END_TIME            = (30*60)/TICK_RATE # for 30 Min

ACCURACY_REDUCTION      = 0.08
HIT_BOX                 = 0.40

#Reversed direction
MAPS = [
    [
    "################",
    "#............W.#",
    "#........#######",
    "#............S.#",
    "#..............#",
    "#.....##.......#",
    "#.....##.......#",
    "#..............#",
    "#.E............#",
    "#..............#",
    "######.........#",
    "#....#.........#",
    "#.S..#.........#",
    "#..........N.###",
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
    '''
    Spawn-Class which handles the occupation of a spawn field
    '''

    def __init__(self, coordinate : Coordinate = Coordinate(3.5,3.5), direction : float = 0):

        self.coordinate = coordinate

        self.direction = direction

        self.lock_time = 0

    def use(self):
        '''
        A spawn is occupied by the player
        '''
        print(F"Spawn at x: {self.coordinate.x} y: {self.coordinate.y} is occupied")

        # The Spawn is occupied for 5 Seconds
        self.lock_time = SPAWN_LOCK_TIME

    def update_occupation(self):
        '''
        Update the status of a spawn
        > -1 means Player is using the Spawn
        '''

        if self.lock_time == 1:
            print(F"Spawn {self} at x: {self.coordinate.x} y: {self.coordinate.y} is free again")

        if(self.lock_time > 0):
            self.lock_time -= 1

class Weapon:

    def __init__(self, name : str, max_ammunition : int, latency : int, dmg : int):

        #print(F"Weapon: {self}")

        self.name :str = name
    
        self.max_ammunition : int = max_ammunition

        self.curr_ammunition : int = max_ammunition

        #How much Frames does the Player have to wait for the next shot
        self.latency : int = latency
        self.curr_latency : int = 0

        #How much damage does the Weapon cause
        self.damage : int = dmg

# List for all available weapons
AVAILABLE_WEAPONS = {
    "P99" : [
        "P99",
        50,             #50 Kugeln in der Waffe
        round(0.8/TICK_RATE),  #Jede 0.8 Sekunden kann geschossen werden
        20              # The weapon reduces 20 health per bullet
    ],
    "MP5" : [
        "MP5",
        200,            #200 Kugeln in der Waffe
        round(0.1/TICK_RATE),  #Jede 0.1 Sekunden kann geschossen werden   
        10              # The Weapon reduces 10 Health per Bullet 
    ],
    "Shotgun" : [
        "Shotgun",
        10,            #200 Kugeln in der Waffe
        round(1.4/TICK_RATE), #Jede 1.4 Sekunden kann geschossen werden   
        50             # The Weapon reduces 50 Health per Bullet 
    ],
}

class Map:
    '''
    Class for handling the map
    It can read a map from strings array
    '''

    def __init__(self, width : int, height : int, map : pd.DataFrame, strings : list[str], spawns : list[Spawn]):
        self.width = width
        self.height = height
        self.map = map
        self.map_string = strings
        self.spawns = spawns
        self.tick = 0
    
    #Helper function for from_list()
    def func(spawns, x, y, char) -> str:

        # Spawn was found
        spawn_flag = False

        # in what direction is the spawn
        dir = 0

        #Check if the direction fits to the coordinate
        # N and S are reversed, so N gets math.pi
        if(char == 'N'):
            spawn_flag              = True
            dir                     = math.pi

        #Check if the direction fits to the coordinate
        if(char == 'E'):

            spawn_flag              = True
            dir                     = math.pi/2
    
        #Check if the direction fits to the coordinate
        # N and S are reversed, so S gets 0
        if(char == 'S'):
            spawn_flag              = True
            dir                     = 0
    
        #Check if the direction fits to the coordinate
        if(char == 'W'):
            spawn_flag              = True
            dir                     = -math.pi/2

        # if spawn was found
        if(spawn_flag):

            char = len(spawns)

            spawns.append(
                Spawn(
                    Coordinate(
                        x + 0.5,
                        y + 0.5,
                    ),
                    dir   
                )
            )

        return char
    
    # validate the input string of map
    # Static Method
    def from_list(strings: list):

        spawns = list()

        #TODO: Anpassen an das gewünschte Format
        map = pd.DataFrame([list(string) for string in strings], dtype='string')

        inv_map = map[map == np.nan].dropna()

        if(not inv_map.empty):
            print(F"Map is invalid: {inv_map}")

        inv_map = map.replace(["#", ".", "W", "S", "N", "E"], np.nan).dropna()

        if(not inv_map.empty):
            print(F"map contains invalid letters: {inv_map}")

        map.apply(lambda x: x.apply(lambda y: Map.func(spawns, x.name, x[x==y].index[0], y)))
        
        '''
        for idx_s, string in enumerate(strings):
            
            #if len(string.replace('#','').replace('.','').replace('N','').replace('E','').replace('S','').replace('W','')) != 0:
            #    print('Map contains invalid values. It only accepts \"#\" or \".\" and spawn fields')

            #Check if Map fits the format
            #if len(string) != len(strings[-1]):
            #    print("Map is invalid")

            

            #Handling for spawns
            for idx_c, char in enumerate(string):

                #print("NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN")

        '''        
            
        if(len(spawns) == 0):
            print("Map contains no spawn fields")

        return Map(
            len(strings[0]),
            len(strings),
            map,
            strings,
            spawns,
        )

    # Check if Object collides with Map
    # Returns True if Oject collide with wall in any way
    def check_collision(self, coordinate : Coordinate, object, dir = 0, tolerance : float = 0.25) -> int | None:        
        '''
        Checks collision for bullets.
        '''

        try:
            
            # Find char on next edge
            e_1 = self.map.iloc[round(coordinate.y - (0.5 + tolerance)), round(coordinate.x - (0.5 + tolerance))]
            e_2 = self.map.iloc[round(coordinate.y - (0.5 + tolerance)), round(coordinate.x - (0.5 - tolerance))]
            e_3 = self.map.iloc[round(coordinate.y - (0.5 - tolerance)), round(coordinate.x - (0.5 + tolerance))]
            e_4 = self.map.iloc[round(coordinate.y - (0.5 - tolerance)), round(coordinate.x - (0.5 - tolerance))] 

            # Check on what edge is a wall
            A = e_1 == "#"
            B = e_2 == "#"
            C = e_3 == "#"
            D = e_4 == "#"

            # if the player moves
            if(type(object).__name__ == "Player"):

                # if the the next field is a spawn

                try:
                    self.spawns[int(e_1)].lock_time = SPAWN_LOCK_TIME
                except ValueError:
                    pass

                try:
                    self.spawns[int(e_2)].lock_time = SPAWN_LOCK_TIME
                except ValueError:
                    pass

                try:
                    self.spawns[int(e_3)].lock_time = SPAWN_LOCK_TIME
                except ValueError:
                    pass

                try:
                    self.spawns[int(e_4)].lock_time = SPAWN_LOCK_TIME
                except ValueError:
                    pass

                a =     A and not B and not C and not D
                b = not A and     B and not C and not D
                c = not A and not B and     C and not D
                d = not A and not B and not C and     D

                look_north_east = dir > 0 and dir <= math.pi/2
                look_south_east = dir > math.pi/2 and dir <= math.pi
                look_north_west = dir <= 0 and dir > -math.pi/2
                look_south_west = dir <= -math.pi/2 and dir > -math.pi

                # Is the player allowed to move in x
                if(
                (not(A and C or B and D) or
                ( a and look_south_east) or
                ( b and look_south_west) or                 
                ( c and look_north_east) or 
                ( d and look_north_west))                     and not
                ( a and (look_north_west or look_south_west)) and not
                ( b and (look_north_east or look_south_east)) and not
                ( c and (look_south_west or look_north_west)) and not 
                ( d and (look_south_east or look_north_east))):
                    object.current_position.x = coordinate.x

                # Is the player allowed to move in y
                if((not (A and B or C and D) or 
                ( a and look_north_west) or 
                ( b and look_north_east) or
                ( c and look_south_west) or 
                ( d and look_south_east))                     and not
                ( a and (look_south_east or look_south_west)) and not 
                ( b and (look_south_west or look_south_east)) and not
                ( c and (look_north_east or look_north_west)) and not 
                ( d and (look_north_west or look_north_east))):
                    object.current_position.y = coordinate.y

                ne = A and B and D
                se = B and C and D
                sw = A and C and D
                nw = A and B and C    

                # If Player is in corner, dont change anything
                if ne or se or sw or nw:
                    #print(F"Player is located at a corner: y: {coordinate.y} x: {coordinate.x}")
                    return
                '''
                if(A or B or C or D):
                    print(F"\nne: {look_north_east}")
                    print(F"se: {look_south_east}")
                    print(F"nw: {look_north_west}")
                    print(F"sw: {look_south_west}")
                    print(F"A: {A}")
                    print(F"B: {B}")
                    print(F"C: {C}")
                    print(F"D: {D}\n")
                ''' 
            else:
                # Is the bullet colliding in x
                if(A and C or B and D):                
                    return True

                # Is bullet colliding in y
                if(A and B or C and D):
                    return True
                
                return False

            #print(F"x: {object.current_position.x} y: {object.current_position.y}")

        except IndexError:
                print(F"Bewegung nach x:{coordinate.x} und y:{coordinate.y} war ungültig und wurde zurückgesetzt!")
                object.current_position = Coordinate(3.5,3.5)
                return True

    # Return für updating the state     
    def render(self) -> Mapping[str, Any]:
        return self.map_string

class Player:
    '''
    Class for handling players
    '''

    # Initiate player
    def __init__(self, username : str, position : Coordinate = Coordinate(3.5,3.5), weapons: list[Weapon] = None, speed : float = PLAYER_SPEED, rotation_speed : float = ROTATION_SPEED, alive : int = 0):
        
        # Initiate the Username
        self.name = username

        self.alive = alive

        # Position is an Object of Coordinate
        self.current_position = position

        # Represents the health
        self.health = 100

        # Represents the angle, in which the player is facing in radians
        self.direction = 0

        # Counts down from a specific number to zero for every tick, when it got activated
        self.justShot = 0

        # Counts down from a specific number to zero for every tick, when it got activated
        self.justHit = 0

        # Represents the current available weapons
        self.weapons : list[Weapon]= [Weapon(*AVAILABLE_WEAPONS["P99"]), Weapon(*AVAILABLE_WEAPONS["MP5"]), Weapon(*AVAILABLE_WEAPONS["Shotgun"])]

        #Represents the current weapon
        #Current Weapon
        self.current_weapon : Weapon = self.weapons[0] 

        self.current_weapon_idx = 0

        self.change_weapon_delay : int = 0

        # Represents score for kill and deaths
        self.kills  = 0
        self.deaths = 0
        self.kill_death = 0

        '''
        Float describes how fast the Player is moving
        '''
        self.speed = speed

        '''Float describes how fast the Player is rotating'''
        self.rotation_speed = rotation_speed

        '''
        Integer how long player has to wait
        if -1 then Player is not participating in Game at all
        '''
        self.alive = 0

        '''
        Counts how many times a player did not send something in a row
        '''
        self.delayed_tick = 0

    def find_spawn(self, map : Map):
        '''
        Find an available Spawn for the Player
        Returns True if found
        Returns False if not found
        '''
        #Did the Player find Spawn?
        flag = False

        map_len = len(map.spawns)

        #print(F"map_len: {map_len}")

        #for spawn in map.spawns:
        #    print(F"spawn {spawn} x: {spawn.coordinate.x} y: {spawn.coordinate.y}")

        rnd_idx = random.randint(0,map_len-1)

        for idx in range(map_len):

            # Start from the rnd Spawn
            spawn = map.spawns[(idx+rnd_idx)%map_len]

            #print(F"x: {spawn.coordinate.x} y: {spawn.coordinate.y}")

            # if the spawn is not yet occupied
            if(spawn.lock_time == 0):
                
                flag = True
                print(F"\nSpawn: x: {spawn.coordinate.x} y: {spawn.coordinate.y}")
                break

        # no available Spawn was found?
        if(not flag):
            print("No spawn was found")
            return False

        #Declare the Spawn as used
        spawn.use()

        self.direction = spawn.direction

        # Initiate the current position
        self.current_position = Coordinate(spawn.coordinate.x,spawn.coordinate.y)

        # Spawn was found
        return True

    def shoot(self, state, move_flag = False):
        '''
        Describes the function to be called when the player shoots
        '''
        
        weapon = self.current_weapon

        if weapon.curr_ammunition > 0 and weapon.curr_latency == 0:

            print(F"{self.name} just shot a bullet!")

            # The animation of shooting shall go on for 1 seconds
            self.justShot = JUST_SHOT_ANIMATION

            # Reduce the current ammo of current weapon by one
            weapon.curr_ammunition -= 1

            # Start the delay of the weapon
            weapon.curr_latency = weapon.latency

            dir = self.direction

            # if the player is moving in that frame, reduce the accuracy
            if(move_flag):

                rnd = random.uniform(-ACCURACY_REDUCTION,ACCURACY_REDUCTION)
                #print(rnd)
                dir += rnd

            # Add bullet to current state
            state.bullets.append(
            Bullet(
                # From whom was a bullet shot?
                self,
                #0.5 Blöcke vom Spieler entfernt entstehen die Bullets
                self.current_position.x + 1 * np.sin(self.direction),
                self.current_position.y + 1 * np.cos(self.direction),
                #Shot in direction of player itself
                dir
            )
        )
        else:
            pass
            #print(F"{self.name} has no bullets: {weapon.curr_ammunition} or latency is still active : {weapon.curr_latency} ")

    def change_weapon(self, idx):
        '''
        Change the weapon by an indicator
        '''
        # if the idx is too high then modulo the length of the weapons
        self.current_weapon_idx = idx % len(self.weapons)

        self.current_weapon = self.weapons[self.current_weapon_idx]

        # Wait 1 seconds to be able to shoot again
        self.change_weapon_delay = CHANGE_WEAPON_DELAY
        
    #Describes the function to be called when the player is hit
    def get_hit(self, state, bullet, mode : int):

        # The animation of getting hit shall go on for 1 second
        self.justHit = JUST_HIT_ANIMATION

        print(F"Player {self.name} is hit by player {bullet.player.name}")

        self.health -= bullet.weapon.damage
        
        if(self.health < 1):
            
            if(mode == 0):

                # increase score of player
                bullet.player.kills +=1

                # Update the kill/death rate
                try:
                    bullet.player.kill_death = bullet.player.kills/bullet.player.deaths
                except ZeroDivisionError:
                    bullet.player.kill_death = bullet.player.kills/1

                # Player is not alive anymore and waits till he respawns
                self.die()

            elif(mode == 1):
                
                # Player is not alive anymore
                self.remove_from_game()
        
        #Remove bullet from State and delete the object
        try:
            state.bullets.remove(bullet)
        except ValueError:
            print("Bullet already gone")

        del(bullet)
            
    #Describes the function to be called when the player moves
    def move(self, state, x : int = 0, y: int = 0):

        #print(F"{self.name} is moving")

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

        #print(F"1 tmp x: {tmp.x} y: {tmp.y}")

        #Move only in direction of max math.pi
        tmp.cod_move(self.speed, dir)

        #print(F"2 tmp x: {tmp.x} y: {tmp.y}")
        #print(F"obj x: {object.current_position.x} y: {object.current_position.y}")

        # Look for collision with other Players
        for player in state.players:

            # if the on-going move is too close to another player then turn the boolean flag
            if(player.name != self.name and tmp.get_distance(player.current_position) < 1):
                
                print(F"Player {self.name} is too close to another player {player.name}")

                too_close = True

        # if player is not too close to an object
        if(not too_close):
            state.map.check_collision(tmp, self, dir = dir)

        #print(F"x: {self.current_position.x} y: {self.current_position.y}")

    '''
        Change the direction of the player by the given direction
    '''
    def change_direction(self, mouseX : float):

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
        #print("Die!")

        # increase the death variable
        self.deaths += 1

        # Update the kill/death rate
        try:
            self.kill_death = self.kills/self.deaths
        # if there is no death at all
        except ZeroDivisionError:
            self.kill_death = self.kills/1

        self.alive = REVIVE_WAITING_TIME

    '''
    Remove the player from Game permanently
    '''
    def remove_from_game(self, value : int = -1):

        self.alive = value

    '''
    Returns all relevant information about the Player for the Client
    '''
    def render(self) -> Mapping[str, Any]:
        return{
            "x"           : self.current_position.x,
            "y"           : self.current_position.y,
            "h"           : self.health,
            "k"           : self.kills,
            "dir"         : self.direction,
            "shot_an"     : self.justShot,
            "hit_an"      : self.justHit,
            "cha_weap_an" : self.change_weapon_delay,
            "weapon"      : self.current_weapon_idx,
            "ammo"        : self.current_weapon.curr_ammunition,
            "alive"       : self.alive,
        }

class Bullet:
    '''
    Creating and handling Bullets
    '''

    # Initiate bullet
    def __init__(self, origin_player : Player, x : float, y : float, direction : float):

        #print("A bullet has been created")

        self.player           : Player     = origin_player
        self.weapon                        = origin_player.current_weapon
        self.prior_position   : Coordinate = Coordinate(x,y)
        self.middle_position  : Coordinate = Coordinate(x,y)
        self.current_position : Coordinate = Coordinate(x,y)

        self.direction : float = direction

        # One Movement per frame
        self.speed : float = BULLET_SPEED

    # Execute for every bullet this function
    # Returns True if bullet collide with Wall
    def update_pos(self, map : Map):

        tmp = deepcopy(self.current_position)

        #print(self.current_position.x, "\n")

        tmp.cod_move(self.speed, self.direction)

        #print(self.current_position.x, "\n")

        # Check collision with Wall
        if map.check_collision(tmp, self, tolerance = 0.05):
            return True
        else:

            #print(F"{self.prior_position}\n{self.middle_position}\n{self.current_position}\n{tmp}\n")

            #if Bullet did not collide with wall
            self.prior_position = deepcopy(self.current_position)

            self.current_position = deepcopy(tmp)

            self.middle_position.x = (self.prior_position.x + self.current_position.x)/2
            self.middle_position.y = (self.prior_position.y + self.current_position.y)/2

            #print(F"{self.prior_position.x}\n{self.middle_position.x}\n{self.current_position.x}\n{tmp.x}\n")

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
        self.players : list[Player] = []#[Player(name, ) for name in players_name]
        self.bullets = bullets
        self.corpses : list[Player] = []


    def render(self) -> Mapping[str, Any]:
        return { 
            "map" :     self.map.render(),
            "players" : {p.name: p.render() for p in self.players},
            "bullets" : [b.render() for b in self.bullets],
            "corpses" : self.corpses,
        }

class GameEngine(threading.Thread):
    '''
    Thread for handling a game
    '''

    # Constructor function for GameEngine
    def __init__(self, group_name, players_name : list[str] = [], map_string = MAPS[0], max_players : int = 6, game_mode : int = 0, win_score : int = 20, end_time : int = MAX_END_TIME):
        
        # Did the game started?
        self.start_flag = False

        self.running = True

        #game_modes
        # 0: Play until one player has enough kills. Revive after 10 Seconds
        # 1: Last man standing, no reviving at all
        self.game_mode = game_mode

        print(F"Initializing GameEngine: {group_name} with players: {players_name}")

        # Create a thread to run the game
        super(GameEngine, self).__init__(daemon = True, name = "GameEngine")

        # the times of total ticks
        self.tick_num = 0

        # random ID for the game
        self.name = uuid.uuid4()

        # group_name for communication
        self.group_name = group_name

        # how many kills are necessary to win the game
        self.win_score = win_score

        # end_time in seconds
        self.end_time  = end_time

        # get all the available channels
        self.channel_layer = get_channel_layer()

        self.event_changes = {}
        self.event_lock = threading.Lock()
        self.player_lock = threading.Lock()

        self.player_queue : list[Player] = []

        #How man players are allowed in the game
        self.max_players = max_players

        map_string = MAPS[0]

        self.state = State(
            Map.from_list(map_string), 
            players_name
            )

    # The main loop for the game engine
    def run(self) -> None:

        print(F"Starting engine loop with self.running: {self.running}")

        # infinite loop
        while self.running:

            if self.start_flag:

                start = time.time()

                # After each tick update the current status of the game
                self.tick()

                # Broadcast the current Status to all players in game
                self.broadcast_state()

                # Sleep for a specific time, in which the game will calculate every new status
                try:
                    time.sleep(TICK_RATE - (time.time() - start))
                except ValueError:
                    print("1", end="")
                    #self.start_flag = False
                    pass


    def broadcast_state(self) -> None: 
        '''
        The broadcast method which broadcast the current game state to the channel
        '''

        # Get the current information about the game state
        state_json = self.state.render()

        #print(state_json)

        # Synchronize the channel's information and send them to all participants
        async_to_sync(self.channel_layer.group_send)(
            self.group_name, 
            {
             "type": "game.update",
             "state": state_json
            }
        )

    def tick(self) -> None:
        ''' 
        Function in which every tick it describes

        '''

        self.tick_num += 1         

        if(self.tick_num >= self.end_time):
            
            # if time limit was reached
            self.time_limit_reached()
        
        #print(F"Tick {self.tick_num} for game {self.name}")

        #start = time.time()

        with self.event_lock:
            events = self.event_changes.copy()
            self.event_changes.clear()

        #end = time.time()

        #print(F"event: {end-start}s\n")

        if self.state.players:
            self.process_players(events)

        #start = time.time()

        #print(F"players: {start-end}s\n")

        if self.state.bullets:
            self.process_bullets()
        
        #end = time.time()

        #print(F"bullets: {end-start}s\n")
        
        self.process_hits()

        #start = time.time()

        #print(F"hits: {start-end}s\n")
        
        self.process_new_players()

        #end = time.time()

        #print(F"new players: {end-start}s\n")

        self.process_spawns()

        #start = time.time()

        #print(F"spawns: {start-end}s\n\n")


    def calculate_distances(self) -> None:
        pass


    def process_players(self, events) -> None:
        '''
        Handle the actions of a player and check the winning conditions
        '''

        # if game is about last man standing and only one Player remained
        if self.game_mode == 1 and len(self.state.players) == 1:

            print("Last Man Standing was won because only one player left")
            # Declare it as a win
            self.win(self.state.players)

        for idx, player in enumerate(self.state.players):

            #if player did not respond for one second or more
            if player.delayed_tick >= PLAYER_DELAY_TOLERANCE:

                player.remove_from_game(-2)

                print(F"Player {player.name} did not respond for one second or more! So he was removed temporarily from GameEngine!")

                #Remove the Player from current Game
                #Add him to the queue
                self.player_queue.append(self.state.players.pop(idx))

                continue

            # if Player died recently and his alive status was changed
            if player.alive > 0:

                # remove him from current game and add him to queue
                self.player_queue.append(self.state.players.pop(idx))

            if self.game_mode == 0 and player.kills >= self.win_score:
                
                print(F"Enough player were killed by {player.name}")
                
                self.win([player])
                
            #print(events.keys())

            if player.name in events.keys():

                #print(F"Process players {self.state.players} with {events}")

                # Does the player move in that frame
                move_flag = False

                if(player.delayed_tick > 1):
                    #print(F"Player {player.name} did not respond for {player.delayed_tick} ticks")

                    #reset the delayed_tick
                    player.delayed_tick = 0

                event = events[player.name]

                player.change_direction(event["mouseDeltaX"])

                # If the player wants to change the weapon                
                if(event["weapon"] != player.current_weapon_idx and len(player.weapons) > 1):

                    player.change_weapon(event["weapon"])

                weapon = player.current_weapon

                if(weapon.curr_latency > 0):
                    # reduce the latency of the current weapon
                    weapon.curr_latency -= 1
                
                if(event["x"] != 0 or event["y"] != 0):
                    move_flag = True
                    player.move(self.state, event["x"], event["y"])

                if(event["leftClick"]):
                    if(player.change_weapon_delay == 0):
                        player.shoot(self.state, move_flag)
                    else:
                        #print("Weapon delay")
                        pass
            elif(player.alive == 0):
                #Increase the delayed tick of the player
                player.delayed_tick += 1
            
            #if the player is currently changing its weapon
            if player.change_weapon_delay > 0:

                #print(player.change_weapon_delay)

                #reduce the delay
                player.change_weapon_delay -= 1
            
    def process_hits(self) -> None:
        '''
        Checks if any bullet hits a player
        '''

        for player in self.state.players:

            for bullet in self.state.bullets:

                dis_1 = bullet.current_position.get_distance(player.current_position)
                dis_2 = bullet.middle_position.get_distance(player.current_position)

                if dis_1 < HIT_BOX or dis_2 < HIT_BOX :
                    
                    #print(F"\nbullet: {bullet}")
                    #print(F"{dis_1} and {dis_2}")

                    # execute the function
                    player.get_hit(self.state, bullet, self.game_mode)


        #[player.get_hit(self, bullet, self.game_mode)  for player in self.state.players for bullet in self.state.bullets if bullet.current_position.get_distance(player.current_position) < 0.1]

    def process_bullets(self) -> None:
        '''
        Checks if bullet hits the wall
        '''
        # Make the next move for all bullets
        # if True then it collide with Wall or Player, so remove it
        for idx, bullet in enumerate(self.state.bullets):
            if bullet.update_pos(self.state.map):
                tmp = self.state.bullets.pop(idx)  
                del tmp

    def process_spawns(self) -> None:
        '''
        Reduce the tick of every Spawn, so new Player can join
        None will be returned
        '''
        #print(F"len spawns: {len(self.state.map.spawns)}")

        [spawn.update_occupation() for spawn in self.state.map.spawns]

    def apply_events(self, player: str, events) -> None:
        '''
        Transfer the changes from the GameConsumer to the GameEngine
        '''

        #print("Applying changes for " + player)
        
        with self.event_lock:
            self.event_changes[player] = events

    def join_game(self, player_name: str) -> None:

        #print(F"\n\nPlayer {player_name} joined game!\n\n", )

        state_p = next((obj for obj in self.state.players if obj.name == player_name), False)
        state_q = next((obj for obj in self.player_queue if obj.name == player_name), False)

        # Look if player is already in the game
        if(state_p):
            if(state_p.delayed_tick < 30):
                #state_p.alive = 0
                state_p.delayed_tick = 0
            else:               
                print(F"\n\nPlayer {player_name} is already in game and playing!\n")
                return
        try:
            # Look if the Player did not disconnect and is still in game
            if(state_q.alive != -2):
                print(F"\n\nPlayer {player_name} is already in game and waiting!\n")
                return  
            # if the Player is disconnected and rejoined the game
            else:
                print(F"\n\nPlayer {player_name} is rejoining the game!\n")
                state_q.alive = PLAYER_WAITING_TIME_AFTER_NOT_RESPONDING
        except:
            print(F"\n\nPlayer {player_name} is joining as new player the game!\n")
            # if the Player joins the game for the first time
            with self.player_lock:
                # Append Player to the queue so it can be appended to the game
                self.player_queue.append(Player(player_name, alive = 0))

    def process_new_players(self) -> None:
        '''
        Look if new Players should join the game
        '''

        #Where is the pointer 
        idx = 0

        for player in self.player_queue:

            # if player is ready to spawn on the battle
            if(player.alive == 0):

                #if spawn is found returns true
                if not player.find_spawn(self.state.map):

                    print("No spawn was found yet")

                    #Wait for specific time if player could not spawn
                    player.alive = PLAYER_WAITING_TIME_OCCUPIED_SPAWN 

                #set his health back to 100
                player.health = 100

                # reset the delayed tick of the rejoined player
                player.delayed_tick = 0

                # add the players to the game
                self.state.players.append(self.player_queue.pop(idx))


                print(player.name)

            # if player is waiting for rejoining
            # -1 Players are not included
            elif player.alive > 0:

                # If the player died in that frame
                if(player.alive == REVIVE_WAITING_TIME):
                    self.state.corpses.append({"username" : player.name, "x" : player.current_position.x, "y" : player.current_position.y, "duration" : JUST_DIED_ANIMATION}) 

                #reduce wait time of player
                player.alive -= 1

                #skip Player for pop() method
                idx += 1
            else:
                #skip Player for pop() method
                idx += 1   

    def process_corpses(self) -> None : 
        '''
        Process the current Corpses on the battlefield
        '''


        for corpse in self.state.corpses:

            if(corpse["duration"] == 0):
                self.state.corpses.remove(corpse)

            corpse["duration"] -= 1 

    def win(self, winning_players : list[Player]) -> None:

        print(F"{winning_players} wins the game")

        # Send the essential information for validate the winner of the game
        async_to_sync(self.channel_layer.send)(
            "game_engine", 
            {
             "type"    : "win",
             "time"    : self.tick_num * TICK_RATE,
             "group"   : self.group_name, 
             "players" : 
             [
                 { "name"       : winning_player.name,
                   "kills"      : winning_player.kills,
                   "deaths"     : winning_player.deaths,
                   "kill_death" : winning_player.kill_death,
                 } 
                   for winning_player in winning_players]
            }
        )

    # When the time has reached its limit
    def time_limit_reached(self): 

        print("the time limit has been reached")

        # if the winner is about the highest kills
        if self.game_mode == 0:

            # Get the best players out of all players and broadcast them
            self.win(self.look_for_best_players(self.state.players + self.player_queue))
        
        elif self.game_mode == 1:

            # Get the best players out of still alive players and broadcast them
            self.win(self.look_for_best_players(self.state.players))

        
    def look_for_best_players(self, players):

        # Look for the highest kills in queue and in current game
        highest_kills = max(players, key=attrgetter('kills')).kills

        # Look for all Players with highest kills
        best_players = [player for player in players if player.kills == highest_kills]

        # if there is only one Player the best player
        if len(best_players) == 1:

           return best_players

        else:

            # Look for the highest kills in queue and in current game
            highest_kill_death = max(best_players, key=attrgetter('kill_death')).kill_death

            # Look for all Players with highest kills
            best_players = [player for player in best_players if player.kill_death == highest_kill_death]   

            return best_players 







                
        
        



