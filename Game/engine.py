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
TICK_RATE = 1/60

PLAYER_SPEED            = TICK_RATE/0.1
ROTATION_SPEED          = TICK_RATE/1
BULLET_SPEED            = TICK_RATE/TICK_RATE


# Every Unit is in Seconds
JUST_SHOT_ANIMATION     = 100
JUST_HIT_ANIMATION      = round(1/TICK_RATE)   # 1 Second
JUST_DIED_ANIMATION     = round(10/TICK_RATE)

CHANGE_WEAPON_DELAY     = round(1/TICK_RATE)   # 1 Second
SPAWN_LOCK_TIME         = round(10/TICK_RATE)  # 10 Seconds
REVIVE_WAITING_TIME     = round(10/TICK_RATE)  # 10 Seconds
PLAYER_DELAY_TOLERANCE  = round(3/TICK_RATE)
PLAYER_WAITING_TIME_AFTER_NOT_RESPONDING = round(10/TICK_RATE)
PLAYER_WAITING_TIME_OCCUPIED_SPAWN = round(0.1/TICK_RATE)

MAX_ENDTIME            = (30*60)/TICK_RATE # for 30 Min

ACCURACY_REDUCTION      = 0.11
HIT_BOX                 = 0.40

#key constants
ammo_key                = 'a'
bullet_key              = 'b'
corpses_key             = 'c'
click_key               = 'c'
duration_key            = 'd'
direction_key           = 'd'
death_key               = 'd'
group_key               = 'g'
health_key              = 'h'
inactive_key            = 'i'
kills_key               = 'k'
killDeath_key           = 'kd'
map_length_key          = 'l'
map_key                 = 'm'
mouseDelta_key          = 'm'
name_key                = 'n'
player_key              = 'p'
state_key               = 's'
time_key                = 't'
weapon_key              = 'w'
x_coordinate_key        = 'x'
y_coordinate_key        = 'y'
justShot_animation      = 's_a'
justHit_animation       = 'h_a'
weapon_change_animation = 'w_a'

#Reversed direction
MAPS = [
    {
        "len" : len("#######################################################################################"),
        "map" :     "#######################################################################################" +
                    "#..S.#.............................#..............###.S......####.......####........W.#" +
                    "#....#............#.E..............#..............###........#................######..#" +
                    "#.####.....####...######...####..........................#...#..#####.........##......#" +
                    "#.............#####...........#..E.......................#..........############......#" +
                    "#..###............#...........###########.....############.#####....#..........#.######" +
                    "###########...................#.S....#..............#......#........#..##......#......#" +
                    "#.S.#.............................#.....#...........###....#........#..##.............#" +
                    "#...#...................#################...........#......#.....####..##..##########.#" +
                    "#...........................W.#.....................#....N.#........#..##......#......#" +
                    "#.....####........#...........#................######.######........#..........#......#" +
                    "#........###......#...........###########...........................#..E.......#.######" +
                    "#........###...####.....###.........................................########...#......#" +
                    "######...#....#####.....###....................................................#......#" +
                    "#.E......#......S.#.....###.....##.##################.........######...........######.#" +
                    "#........######...#.............##.#.S..#.....#...W.#.........######...........#....S.#" +
                    "###......######...#.............##.#..###.....#..########.....######...........#......#" +
                    "#....#..........................##.#................#.............E............###.####" +
                    "#..###..................#.......##.########..##.....#..........................#......#" +
                    "#..###..........######..#.......##............#................#######...#######......#" +
                    "#....#..........#.S.....#.......####.E........#.....#..........#...............#.######" +
                    "#....####.......#....####.#........###.######.###.#######...####...............#......#" +
                    "###..#..........#....#....#..........#.#......#...#............#..#########...........#" +
                    "###..####............#..N.#..........#.#..#...#.#.#............#...............######.#" +
                    "#....#..........######.####..........#.#..#.N...#.#######......#...............#......#" +
                    "#..W.#...............#...............#.#..#######..............###.....#########....W.#" +
                    "#..###...............#..........................#............W.#.......#.......#.######" +
                    "#..###...............#############.............##.....##########...............#......#" +
                    "#....#............#........................................#####...............#......#" +
                    "#....###########..#.########...............................#####.....#####...########.#" +
                    "#....#............#..E.....#..##...####....###....####...................#............#" +
                    "#.................#.###....####.......#....###....#......................#...#####....#" +
                    "####..#############...#...............#....###....#........#.............#.......#..###" +
                    "#......#...#......#.#.#####...#.......#.........W.#........#.......#######.......#....#" +
                    "####...#...##.#.###.#.....#...############.....#########...#...#.........#.......#..###" +
                    "#.S#.......#........#####.#......#.S.....##...##.......#####...#.........#####.#.#....#" +
                    "#.. .......#.....##.......#..........#............##.........N##...............#....N.#" +
                    "#######################################################################################",
    },
    {
        "len" : len("################"),
        "map" : "################" +
                "#............W.#" +
                "#........#######" +
                "#............S.#" +
                "#..............#" +
                "#.....##.......#" +
                "#.....##.......#" +
                "#..............#" +
                "#.E............#" +
                "#..............#" +
                "######.........#" +
                "#....#.........#" +
                "#.S..#.........#" +
                "#..........N.###" +
                "#............###" +
                "################"
    }
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
        #print(F"Spawn at x: {self.coordinate.x} y: {self.coordinate.y} is occupied")

        # The Spawn is occupied for 5 Seconds
        self.lock_time = SPAWN_LOCK_TIME

    def update_occupation(self):
        '''
        Update the status of a spawn
        > -1 means Player is using the Spawn
        '''

        if self.lock_time == 1:
            pass
            #print(F"Spawn {self} at x: {self.coordinate.x} y: {self.coordinate.y} is free again")

        if(self.lock_time > 0):
            self.lock_time -= 1

class Weapon:

    def __init__(self, name : str, maxAmmunition : int, latency : int, dmg : int):

        #print(F"Weapon: {self}")

        self.name :str = name
    
        self.maxAmmunition : int = maxAmmunition

        self.currAmmunition : int = maxAmmunition

        #How much Frames does the Player have to wait for the next shot
        self.latency : int = latency
        self.currLatency : int = 0

        #How much damage does the Weapon cause
        self.damage : int = dmg

# List for all available weapons
AVAILABLE_WEAPONS = {
    "P99" : [
        "P99",
        50,             #50 Kugeln in der Waffe
        round(0.25/TICK_RATE),  #Jede 0.8 Sekunden kann geschossen werden
        20              # The weapon reduces 20 health per bullet
    ],
    "MP5" : [
        "MP5",
        200,            #200 Kugeln in der Waffe
        round(0.08/TICK_RATE),  #Jede 0.1 Sekunden kann geschossen werden   
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

    def __init__(self, width : int, height : int, map : list[list[str]], mapString : str, spawns : list[Spawn]):
        self.width      = width
        self.height     = height
        self.map        = map
        self.mapString  = mapString
        self.spawns     = spawns
        self.tick       = 0
    
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
    def from_list(mapDict : dict[str]):

        spawns = list()

        char_count = len(mapDict["map"])

        width  = mapDict["len"]
        height = char_count/mapDict["len"]

        #TODO: Anpassen an das gewünschte Format
        #map = pd.DataFrame([list(string) for string in strings], dtype='string')

        #inv_map = map[map == np.nan].dropna()

        #if(not inv_map.empty):
        #    print(F"Map is invalid: {inv_map}")

        inv_map = mapDict["map"].replace("#","").replace(".","").replace("W","").replace("S","").replace("N","").replace("E","")

        mapString = mapDict["map"]

        if(len(inv_map) != 0):
            print(F"map contains invalid letters: >>>{inv_map}<<<<")

        # Look for spawns in the map
        for dir in [('N', math.pi), ('E', math.pi/2), ('S', 0), ('W', -math.pi/2)]:

            #print(dir)
            idx = 0

            while idx < char_count:

                idx = mapString.find(dir[0])
                
                if idx == -1:
                    break

                mapString = mapString.replace(dir[0], F"{len(spawns)}", 1)

                x = idx % width
                y = (idx - x)/width

                spawns.append(
                    Spawn(
                        Coordinate(
                            x + 0.5,
                            y + 0.5,
                        ),
                        dir[1]   
                    )
                )

        map = []

        [map.append(list(mapDict["map"][sub-width:sub])) for sub in range(width, char_count + width, width) ]
                         
        if(len(spawns) == 0):
            print("Map contains no spawn fields")

        return Map(
            width,
            height,
            map,
            mapDict["map"],
            spawns,
        )

    # Check if Object collides with Map
    # Returns True if Oject collide with wall in any way
    def check_collision(self, coordinate : Coordinate, object, dir : float = 0, tolerance : float = 0.25) -> int | None:        
        '''
        Checks collision for bullets.
        '''

        try:
            
            # Find char on next edge
            e_1 = self.map[round(coordinate.y - (0.5 + tolerance))][round(coordinate.x - (0.5 + tolerance))]
            e_2 = self.map[round(coordinate.y - (0.5 + tolerance))][round(coordinate.x - (0.5 - tolerance))]
            e_3 = self.map[round(coordinate.y - (0.5 - tolerance))][round(coordinate.x - (0.5 + tolerance))]
            e_4 = self.map[round(coordinate.y - (0.5 - tolerance))][round(coordinate.x - (0.5 - tolerance))] 

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
                    object.currentPosition.x = coordinate.x

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
                    object.currentPosition.y = coordinate.y

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

            #print(F"x: {object.currentPosition.x} y: {object.currentPosition.y}")

        except IndexError:
                print(F"Bewegung nach x:{coordinate.x} und y:{coordinate.y} war ungültig und wurde zurückgesetzt!")
                object.currentPosition = Coordinate(3.5,3.5)
                return True

    # Return für updating the state     
    def render(self) -> Mapping[str, Any]:
        return {
            map_length_key : self.width,
            map_key        : self.mapString,
        }

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
        self.currentPosition = position

        # Represents the health
        self.health = 100

        # Represents the angle, in which the player is facing in radians
        self.direction = 0

        # Counts down from a specific number to zero for every tick, when it got activated
        self.justShot = -1

        # Counts down from a specific number to zero for every tick, when it got activated
        self.justHit = 0

        # Represents the current available weapons
        self.weapons : list[Weapon]= [Weapon(*AVAILABLE_WEAPONS["P99"]), Weapon(*AVAILABLE_WEAPONS["MP5"]), Weapon(*AVAILABLE_WEAPONS["Shotgun"])]

        #Represents the current weapon
        #Current Weapon
        self.currentWeapon : Weapon = self.weapons[0] 

        self.currentWeaponIdx = 0

        self.changeWeaponDelay : int = 0

        # Represents score for kill and deaths
        self.kills  = 0
        self.deaths = 0
        self.killDeath = 0

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
        self.delayedTick = 0

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
                #print(F"\nSpawn: x: {spawn.coordinate.x} y: {spawn.coordinate.y}")
                break

        # no available Spawn was found?
        if(not flag):
            print("No spawn was found")
            return False

        #Declare the Spawn as used
        spawn.use()

        self.direction = spawn.direction

        # Initiate the current position
        self.currentPosition = Coordinate(spawn.coordinate.x,spawn.coordinate.y)

        # Spawn was found
        return True

    def shoot(self, state, move_flag = False):
        '''
        Describes the function to be called when the player shoots
        '''
        
        weapon = self.currentWeapon

        if weapon.currAmmunition > 0 and weapon.currLatency == 0:

            #print(F"{self.name} just shot a bullet!")

            # The animation of shooting
            self.justShot = JUST_SHOT_ANIMATION

            # Reduce the current ammo of current weapon by one
            weapon.currAmmunition -= 1

            # Start the delay of the weapon
            weapon.currLatency = weapon.latency

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
                self.currentPosition.x + 1 * np.sin(self.direction),
                self.currentPosition.y + 1 * np.cos(self.direction),
                #Shot in direction of player itself
                dir
            )
        )
        else:
            pass
            #print(F"{self.name} has no bullets: {weaponA} or latency is still active : {weapon.curr_latency} ")

    def change_weapon(self, idx):
        '''
        Change the weapon by an indicator
        '''
        # if the idx is too high then modulo the length of the weapons
        self.currentWeaponIdx = idx % len(self.weapons)

        self.currentWeapon = self.weapons[self.currentWeaponIdx]

        # Wait 1 seconds to be able to shoot again
        self.changeWeaponDelay = CHANGE_WEAPON_DELAY
        
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
                    bullet.player.killDeath = bullet.player.kills/bullet.player.deaths
                except ZeroDivisionError:
                    bullet.player.killDeath = bullet.player.kills/1

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

        tmp = Coordinate(self.currentPosition.x, self.currentPosition.y)

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
        #print(F"obj x: {object.currentPosition.x} y: {object.currentPosition.y}")

        # Look for collision with other Players
        for player in state.players:

            # if the on-going move is too close to another player then turn the boolean flag
            if(player.name != self.name and tmp.get_distance(player.currentPosition) < 1):
                
                print(F"Player {self.name} is too close to another player {player.name}")

                too_close = True

        # if player is not too close to an object
        if(not too_close):
            state.map.check_collision(tmp, self, dir = dir)

        #print(F"x: {self.currentPosition.x} y: {self.currentPosition.y}")

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
            self.killDeath = self.kills/self.deaths
        # if there is no death at all
        except ZeroDivisionError:
            self.killDeath = self.kills/1

        self.alive = REVIVE_WAITING_TIME

    '''
    Remove the player from Game permanently
    '''
    def remove_from_game(self, value : int = -1):

        self.alive = value

    '''
    Returns all relevant information about the player for the Client
    '''
    def render(self) -> Mapping[str, Any]:

        return{
            x_coordinate_key        : self.currentPosition.x,
            y_coordinate_key        : self.currentPosition.y,
            health_key              : self.health,
            kills_key               : self.kills,
            direction_key           : self.direction,
            justShot_animation      : self.justShot,
            justHit_animation       : self.justHit,
            weapon_change_animation : self.changeWeaponDelay,
            weapon_key              : self.currentWeaponIdx,
            ammo_key                : self.currentWeapon.currAmmunition,
            #"alive"       : self.alive,
        }

    '''
    Returns all relelvant information about the inactive player for the client
    '''
    def render_inactive(self) -> Mapping[str, Any]:
        return{
            state_key : self.alive
        }

class Bullet:
    '''
    Creating and handling Bullets
    '''

    # Initiate bullet
    def __init__(self, originPlayer : Player, x : float, y : float, direction : float):

        #print("A bullet has been created")

        self.player           : Player     = originPlayer
        self.weapon                        = originPlayer.currentWeapon
        self.priorPosition    : Coordinate = Coordinate(x,y)
        self.middlePosition   : Coordinate = Coordinate(x,y)
        self.currentPosition  : Coordinate = Coordinate(x,y)

        self.direction        : float      = direction

        # One Movement per frame
        self.speed : float = BULLET_SPEED

    # Execute for every bullet this function
    # Returns True if bullet collide with Wall
    def update_pos(self, map : Map):

        tmp = deepcopy(self.currentPosition)

        #print(self.currentPosition.x, "\n")

        tmp.cod_move(self.speed, self.direction)

        #print(self.currentPosition.x, "\n")

        # Check collision with Wall
        if map.check_collision(tmp, self, tolerance = 0.15):
            return True
        else:

            #print(F"{self.prior_position}\n{self.middle_position}\n{self.currentPosition}\n{tmp}\n")

            #if Bullet did not collide with wall
            self.priorPosition = deepcopy(self.currentPosition)

            self.currentPosition = deepcopy(tmp)

            self.middlePosition.x = (self.priorPosition.x + self.currentPosition.x)/2
            self.middlePosition.y = (self.priorPosition.y + self.currentPosition.y)/2

            #print(F"{self.prior_position.x}\n{self.middle_position.x}\n{self.currentPosition.x}\n{tmp.x}\n")

            return False


    # If information is requested for rendering and update the game
    def render(self) -> Mapping[str, Any]:
        return {
            x_coordinate_key : self.currentPosition.x,
            y_coordinate_key : self.currentPosition.y
        }

class State:
    '''
    Class for handling the states of the game
    '''

    def __init__(self, map : Map):
        self.map     : Map          = map
        self.players : list[Player] = []#[Player(name, ) for name in playersName]
        self.bullets : list[Bullet] = []
        self.corpses : dict[Player] = []


    def render(self) -> Mapping[str, Any]:
        return { 
            map_key : self.map.render(),
            player_key : {p.name: p.render() for p in self.players},
            bullet_key : [b.render() for b in self.bullets],
            corpses_key : self.corpses,
        }

class GameEngine(threading.Thread):
    '''
    Thread for handling a game
    '''

    # Constructor function for GameEngine
    def __init__(self, lobbyname, mapString = None, playersName : list[str] = [], maxPlayers : int = 6, gameMode : int = 0, winScore : int = 20, endTime : int = MAX_ENDTIME):
        
        # Did the game started?
        self.startFlag = False

        self.running = True

        #game_modes
        # 0: Play until one player has enough kills. Revive after 10 Seconds
        # 1: Last man standing, no reviving at all
        self.gameMode = gameMode

        #print(F"Initializing GameEngine: {lobbyname} with players: {playersName}")

        # Create a thread to run the game
        super(GameEngine, self).__init__(daemon = True, name = "GameEngine")

        # the times of total ticks
        self.tickNum = 0

        # random ID for the game
        self.name = uuid.uuid4()

        # groupName for communication
        self.groupName = lobbyname

        # how many kills are necessary to win the game
        self.winScore = winScore

        # endTime in seconds
        self.endTime  = endTime

        # get all the available channels
        self.channelLayer = get_channel_layer()

        self.eventChanges = {}
        self.eventLock = threading.Lock()
        self.playerLock = threading.Lock()

        self.playerQueue : list[Player] = []

        #How man players are allowed in the game
        self.maxPlayers = maxPlayers

        mapString = MAPS[1]

        self.state = State(
            Map.from_list(mapString), 
            playersName
            )

    # The main loop for the game engine
    def run(self) -> None:

        #print(F"Starting engine loop with self.running: {self.running}")

        # infinite loop
        while self.running:

            if self.startFlag:

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
                    #self.startFlag = False
                    pass

    '''
    Broadcast every important information about the state
    '''
    def broadcast_state(self) -> None: 
        '''
        The broadcast method which broadcast the current game state to the channel
        '''

        #print(stateJson)

        # Get the current information about the game state
        stateJson = self.state.render()

        stateJson[inactive_key] = {player.name : player.render_inactive() for player in self.playerQueue}

        # Synchronize the channel's information and send them to all participants
        async_to_sync(self.channelLayer.group_send)(
            self.groupName, 
            {
             "type": "game.update",
             state_key   : stateJson
            }
        )

    def tick(self) -> None:
        ''' 
        Function in which every tick it describes

        '''

        self.tickNum += 1         

        if(self.tickNum >= self.endTime):
            
            # if time limit was reached
            self.time_limit_reached()
        
        #print(F"Tick {self.tickNum} for game {self.name}")

        #start = time.time()

        with self.eventLock:
            events = self.eventChanges.copy()
            self.eventChanges.clear()

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

        if self.state.corpses:
            self.process_corpses()
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
        if self.gameMode == 1 and len(self.state.players) == 1:

            print("Last Man Standing was won because only one player left")
            # Declare it as a win
            self.win(self.state.players)

        for idx, player in enumerate(self.state.players):

            #if player did not respond for one second or more
            if player.delayedTick >= PLAYER_DELAY_TOLERANCE:

                player.remove_from_game(-2)

                print(F"Player {player.name} did not respond for one second or more! So he was removed temporarily from GameEngine!")

                #Remove the Player from current Game
                #Add him to the queue
                self.playerQueue.append(self.state.players.pop(idx))

                continue

            # if Player died recently and his alive status was changed
            if player.alive > 0:

                # remove him from current game and add him to queue
                self.playerQueue.append(self.state.players.pop(idx))

            if self.gameMode == 0 and player.kills >= self.winScore:
                
                print(F"Enough player were killed by {player.name}")
                
                self.win([player])
                
            #print(events.keys())

            if player.name in events.keys():

                #print(F"Process players {self.state.players} with {events}")

                # Does the player move in that frame
                move_flag = False

                event = events[player.name]

                player.change_direction(event[mouseDelta_key])

                # If the player wants to change the weapon                
                if(event[weapon_key] != player.currentWeaponIdx and len(player.weapons) > 1):

                    player.change_weapon(event[weapon_key])

                weapon = player.currentWeapon

                if(player.delayedTick > 1):
                    #print(F"Player {player.name} did not respond for {player.delayedTick} ticks")

                    #reset the delayedTick
                    player.delayedTick = 0


                # reduce currLatency counter if needed
                if(weapon.currLatency > 0):

                    # reduce the latency of the current weapon
                    weapon.currLatency -= 1
                
                # reduce justShot counter if needed
                if(player.justShot > 0):

                    player.justShot -= round(JUST_SHOT_ANIMATION/player.currentWeapon.latency)

                    if (player.justShot <= 0):
                        player.justShot = -1

                # reduce justHit counter if needed  
                if(player.justHit > 0):

                    player.justHit  -= 1

                #if the player is currently changing its weapon
                if player.changeWeaponDelay > 0:

                    #reduce the delay
                    player.changeWeaponDelay -= 1

                if(event[x_coordinate_key] != 0 or event[y_coordinate_key] != 0):
                    move_flag = True
                    player.move(self.state, event[x_coordinate_key], event[y_coordinate_key])

                if(event[click_key]):
                    if(player.changeWeaponDelay == 0):
                        player.shoot(self.state, move_flag)
                    else:
                        #print("Weapon delay")
                        pass
            elif(player.alive == 0):
                #Increase the delayed tick of the player
                player.delayedTick += 1
                        
    def process_hits(self) -> None:
        '''
        Checks if any bullet hits a player
        '''

        [player.get_hit(self.state, bullet, self.gameMode) for player in self.state.players for bullet in self.state.bullets if bullet.currentPosition.get_distance(player.currentPosition) < HIT_BOX or bullet.middlePosition.get_distance(player.currentPosition) < HIT_BOX]

        '''
        for player in self.state.players:

            for bullet in self.state.bullets:

                dis_1 = bullet.currentPosition.get_distance(player.currentPosition)
                dis_2 = bullet.middlePosition.get_distance(player.currentPosition)

                if dis_1 < HIT_BOX or dis_2 < HIT_BOX :
                    
                    #print(F"\nbullet: {bullet}")
                    #print(F"{dis_1} and {dis_2}")

                    # execute the function
                    player.get_hit(self.state, bullet, self.gameMode)
        '''

    def process_bullets(self) -> None:
        '''
        Checks if bullet hits the wall
        '''

        [self.state.bullets.pop(idx) for idx, bullet in enumerate(self.state.bullets) if bullet.update_pos(self.state.map)].clear()

        # Make the next move for all bullets
        # if True then it collide with Wall or Player, so remove it
        #for idx, bullet in enumerate(self.state.bullets):
        #    if bullet.update_pos(self.state.map):
        #        tmp = self.state.bullets.pop(idx)  
        #        del tmp

    def process_corpses(self) -> None : 
        '''
        Process the current Corpses on the battlefield
        '''

        for corpse in self.state.corpses:

            if(corpse[duration_key] == 0):
                self.state.corpses.remove(corpse)

            corpse[duration_key] -= 1 

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
        
        with self.eventLock:
            self.eventChanges[player] = events

    def join_game(self, playerName: str) -> None:

        #print(F"\n\nPlayer {playerName} joined game!\n\n", )

        stateP = next((obj for obj in self.state.players if obj.name == playerName), False)
        stateQ = next((obj for obj in self.playerQueue if obj.name == playerName),False)

        # Look if player is already in the game
        if(stateP):
            if(stateP.delayedTick < 30):
                #stateP.alive = 0
                stateP.delayedTick = 0
            else:               
                print(F"\n\nPlayer {playerName} is already in game and playing!\n")
                return
        try:
            # Look if the Player did not disconnect and is still in game
            if(stateQ.alive != -2):
                print(F"\n\nPlayer {playerName} is already in game and waiting!\n")
                return  
            # if the Player is disconnected and rejoined the game
            else:
                print(F"\n\nPlayer {playerName} is rejoining the game!\n")
                stateQ.alive = PLAYER_WAITING_TIME_AFTER_NOT_RESPONDING
        except:
            #print(F"\n\nPlayer {playerName} is joining as new player the game!\n")
            # if the Player joins the game for the first time
            with self.playerLock:
                # Append Player to the queue so it can be appended to the game
                self.playerQueue.append(Player(playerName, alive = 0))

    def process_new_players(self) -> None:
        '''
        Look if new Players should join the game
        '''

        #Where is the pointer 
        idx = 0

        for player in self.playerQueue:

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
                player.delayedTick = 0

                # add the players to the game
                self.state.players.append(self.playerQueue.pop(idx))


                print(player.name)

            # if player is waiting for rejoining
            # -1 Players are not included
            elif player.alive > 0:

                # If the player died in that frame
                if(player.alive == REVIVE_WAITING_TIME):

                    print(F"{player.name} was added to the corpses")

                    self.state.corpses.append(
                        {
                            player_key       : player.name, 
                            x_coordinate_key : player.currentPosition.x, 
                            y_coordinate_key : player.currentPosition.y, 
                            duration_key     : JUST_DIED_ANIMATION,
                        }) 

                #reduce wait time of player
                player.alive -= 1

                #skip Player for pop() method
                idx += 1
            else:
                #skip Player for pop() method
                idx += 1   

    def win(self, winningPlayers : list[Player]) -> None:

        print(F"{winningPlayers} wins the game")

        # Send the essential information for validate the winner of the game
        async_to_sync(self.channelLayer.send)(
            "game_engine", 
            {
             "t"    : "w",
             time_key    : self.tickNum * TICK_RATE,
             group_key   : self.groupName, 
             player_key : 
             [
                 { 
                   name_key       : winningPlayer.name,
                   kills_key      : winningPlayer.kills,
                   death_key      : winningPlayer.deaths,
                   killDeath_key  : winningPlayer.killDeath,
                 } 
                   for winningPlayer in winningPlayers]
            }
        )

    # When the time has reached its limit
    def time_limit_reached(self): 

        print("the time limit has been reached")

        # if the winner is about the highest kills
        if self.gameMode == 0:

            # Get the best players out of all players and broadcast them
            self.win(self.look_for_best_players(self.state.players + self.playerQueue))
        
        elif self.gameMode == 1:

            # Get the best players out of still alive players and broadcast them
            self.win(self.look_for_best_players(self.state.players))

        
    def look_for_best_players(self, players : list[Player]):

        # Look for the highest kills in queue and in current game
        highest_kills = max(players, key=attrgetter('kills')).kills

        # Look for all Players with highest kills
        bestPlayers = [player for player in players if player.kills == highest_kills]

        # if there is only one Player the best player
        if len(bestPlayers) == 1:

           return bestPlayers

        else:

            # Look for the highest kills in queue and in current game
            highestKillDeath = max(bestPlayers, key=attrgetter('killDeath')).killDeath

            # Look for all Players with highest kills
            bestPlayers = [player for player in bestPlayers if player.killDeath == highestKillDeath]   

            return bestPlayers 







                
        
        



