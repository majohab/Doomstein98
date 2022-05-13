import math
from operator import attrgetter
import random
import threading
import time
import uuid
import numpy as np
from typing import Any, Mapping

from lobby.models import (Map       as MapDB, 
                          Statistic as StatisticDB,
                          WeaponStatistic, 
                          Weapon    as WeaponDB, 
                          Setting   as SettingDB
)

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from copy import deepcopy

#region config

#key constants
ammo_key                = 'a'
mov_b_anim_key          = 'b'
bullet_key              = 'b'
corpses_key             = 'c'
click_key               = 'c'
dead_key                = 'd'
died_anim_key           = 'd'
duration_key            = 'd'
death_key               = 'd'
event_key               = 'e'
group_key               = 'g'
hit_anim_key            = 'h'
health_key              = 'h'
inactive_key            = 'i'
kills_key               = 'k'
killer_key              = 'k'
killDeath_key           = 'kd'
map_length_key          = 'l'
direction_move_key      = 'm'
map_key                 = 'm'
mouseDelta_key          = 'm'
name_key                = 'n'
mov_p_anim_key          = 'p'
player_key              = 'p'
state_key               = 's'
shot_anim_key           = 's'
time_key                = 't'
type_key                = 't'
direction_view_key      = 'v'
weapon_key              = 'w'
x_coordinate_key        = 'x'
y_coordinate_key        = 'y'
init_key                = 'y'
justShot_animation      = 's_a'
justHit_animation       = 'h_a'
move_animation_key      = 'm_a'
weapon_change_animation = 'w_a'
win_key                 = 'w'

# List of default map
"""
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
                "#.M..........W.#" +
                "#........#######" +
                "#............S.#" +
                "#..............#" +
                "#.....##.......#" +
                "#.....##M......#" +
                "#..............#" +
                "#.E............#" +
                "#..............#" +
                "######.M.......#" +
                "#....#.........#" +
                "#.S..#.........#" +
                "#..........N.###" +
                "#............###" +
                "################"
    }
]
"""

MAP = [
   {
       "len" : map.len,
       "map" : map.string,
    }
    for map in MapDB.objects.all()
]

# List for all available weapons
"""
AVAILABLE_WEAPONS = {
    0 : [
        "Pistol",
        50,             #50 Kugeln in der Waffe
        round(0.3/s.tick_rate),  #Jede 0.8 Sekunden kann geschossen werden
        20,             # The weapon reduces 20 health per bullet
        True
    ],
    1 : [
        "Chaingun",
        200,            #200 Kugeln in der Waffe
        round(0.1/s.tick_rate),  #Jede 0.1 Sekunden kann geschossen werden   
        10,              # The Weapon reduces 10 Health per Bullet 
        True
    ],
    2 : [
        "Shotgun",
        10,            #200 Kugeln in der Waffe
        round(1.4/s.tick_rate), #Jede 1.4 Sekunden kann geschossen werden   
        50,             # The Weapon reduces 50 Health per Bullet 
        True
    ],
}
"""

#endregion

class Coordinate:
    """
    Class to handle movement and distance calculations
    """

    def __init__(self, x : float, y : float):
        """Initiate an object by its two coordinates

        Args:
            x (float): x-coordinate
            y (float): y-coordinate
        """
        
        self.x = x
        self.y = y

    def cod_move(self, speed : float, dir : float) -> None:
        """Moves the coordinate with a specific speed in the specific direction

        Args:
            speed (float, optional): Unit: blocks per frame. Defaults to 0.
            dir (float, optional): _description_. Defaults to 0.
        """

        # If direction is   0° then the object only moves on y axis in positive direction
        # If direction is  90° then the object only moves on x axis in positive direction
        # If direction is 180° then the object only moves on y axis in negative direction
        # If direction is 270° then the object only moves on x axis in negative direction
        self.x += speed * np.sin(dir)
        self.y += speed * np.cos(dir)
  
    def get_distance(self, sec_cod) -> float:
        """Returns the distance between two coordinates

        Args:
            sec_cod (Coordiante): other coordinate

        Returns:
            float: the distance in blocks
        """

        return math.sqrt((self.x - sec_cod.x) ** 2 + (self.y - sec_cod.y) ** 2)

class Spawn:
    """
    Spawn-Class which handles the occupation of a spawn field
    """

    def __init__(self, 
                engine,
                coordinate : Coordinate, 
                direction : float):
        """Creating an object of spawn for a map

        Args:
            coordinate (Coordinate, optional): On what coordinates is the spawn. Defaults to Coordinate(3.5,3.5).
            direction (float, optional): the direction in radians in which the player should look if he spawns there. Defaults to 0.
        """

        # assign engine to itself
        self.engine     = engine

        self.coordinate = coordinate
        self.direction  = direction
        self.lock_time  = 0  

    def use(self) -> None:
        """
        Is called when a spawn is occupied by the player
        """
        
        #print(F"Spawn at x: {self.coordinate.x} y: {self.coordinate.y} is occupied")

        # The Spawn is occupied for 5 Seconds
        self.lock_time = round(self.engine.s.spawn_lock_time/self.engine.s.tick_rate)

    def update(self) -> None:
        """
        Update the status of a spawn
        > -1 means Player is using the Spawn
        """

        if self.lock_time == 1:
            pass
            #print(F"Spawn {self} at x: {self.coordinate.x} y: {self.coordinate.y} is free again")

        if(self.lock_time > 0):
            self.lock_time -= 1

class Bullet:
    """
    Creating and handling Bullets, inlcuding moving and rendering
    """

    def __init__    (self,
                    engine, 
                    originPlayer, 
                    x : float, 
                    y : float, 
                    direction : float):

        # assign engine to itself
        self.engine                        = engine

        self.player           : Player     = originPlayer
        self.weapon                        = originPlayer.currentWeapon
        self.priorPosition    : Coordinate = Coordinate(x,y)
        self.middlePosition   : Coordinate = Coordinate(x,y)
        self.currentPosition  : Coordinate = Coordinate(x,y)

        self.moveAnim         : int        = self.engine.s.move_animation_bullet_modulo
        self.dirMove          : float      = direction

        # One Movement per frame
        self.speed : float = self.engine.s.bullet_speed

    def update_pos  (self)  -> bool:
        """
        Updates the position of every bullet

        Args:
            map (Map): The map object to check collision

        Returns:
            bool: If bullet should be deleted because of collision
        """

        tmp = deepcopy(self.currentPosition)

        #print(self.currentPosition.x, "\n")

        tmp.cod_move(self.speed, self.dirMove)

        #print(self.currentPosition.x, "\n")

        # Check collision with Wall
        if self.engine.state.map.check_collision(tmp, self, tolerance = self.engine.s.wall_hit_box_bullet_tolerance):
            return True
        else:

            #if Bullet did not collide with wall
            self.priorPosition = deepcopy(self.currentPosition)

            self.currentPosition = deepcopy(tmp)

            self.middlePosition.x = (self.priorPosition.x + self.currentPosition.x)/2
            self.middlePosition.y = (self.priorPosition.y + self.currentPosition.y)/2

            self.moveAnim = (self.moveAnim + 1) % self.engine.s.move_animation_bullet_modulo # increase the value by one if he moves

            return False

    def render      (self)       -> Mapping[str, Any]:
        """
        Returns all relevant information for the client to render the bullet

        Returns:
            Mapping[str, Any]: contains all relevant information for the client
        """

        return {
            x_coordinate_key   : self.currentPosition.x,
            y_coordinate_key   : self.currentPosition.y,
            direction_view_key : self.dirMove,
            move_animation_key : self.moveAnim,
        }

class AmmunitionPack:
    """
    Class for munition packs on the battlefield which can be collected
    """

    def __init__(self, engine, coordinate : Coordinate):
        """Creates a munition object

        Args:
            coordinate (Coordinate): position of the munition pack
        """

        self.engine                     = engine
        self.coordinate : Coordinate    = coordinate
        self.weapon     : dict[int:str] = random.choice(self.engine.available_weapons)
        self.ammo       : int           = int(random.randrange(int(self.weapon[1]*self.engine.s.min_munition), int(self.weapon[1]*self.engine.s.max_munition), int(self.weapon[1]*self.engine.s.step_munition)))
        self.max_delay  : int           = int((self.engine.s.default_ammunition_delay * 60)/self.engine.s.tick_rate)
        self.curr_delay : int           = self.engine.s.default_ammunition_delay

        print(F'''
        coordinate  : {self.coordinate.x} {self.coordinate.y}
        ammo        : {self.ammo}
        weapon      : {self.weapon}
        ''')

    def collected(self, player)                         -> None:
        """Called when a player collects a munition package

        Args:
            player (Player): the player who collects the ammunition
        """

        # If the ammunition is not active yet, go back
        if(self.curr_delay > 0):
            return


        print("Munition is collected")

        # Deactivate the the ammunition reset the delay
        self.curr_delay = self.max_delay

        # find the weapon
        pWeapon : Weapon = [weapon for weapon in player.weapons.values() if weapon.name == self.weapon[0]][0]

        # increase the ammunition of the player's weapon
        pWeapon.currAmmunition += self.ammo
        
        # update the ammunition statistic
        pWeapon.refilledAmmo += self.ammo

        # if the currAmmunition is too high then reduce it to the max
        if(pWeapon.currAmmunition > pWeapon.maxAmmunition):
            pWeapon.currAmmunition = pWeapon.maxAmmunition 

    def update(self)                                    -> None:
        """
        Update the the waiting time for spawning again
        """

        # if the ammunitionPack has to wait
        if(self.curr_delay > 0):

            # if the spawn is going to appear again, choose a new weapon with new amount of ammunition
            if(self.curr_delay == 1):

                print(F"{self.weapon[1]} munition was spawnd at x: {self.coordinate.x} y: {self.coordinate.y} with {self.ammo} bullets")

                self.weapon = random.choice(self.engine.available_weapons)
                self.ammo   = int(random.randrange(int(self.weapon[1]*self.engine.s.min_munition), int(self.weapon[1]*self.engine.s.max_munition), int(self.weapon[1]*self.engine.s.step_munition)))

            #reduce it by one
            self.curr_delay -= 1

    def render(self)                                    -> Mapping[str, Any]:
        """
        Returns the relevant informatione about AmmunitionPack

        Returns:
            Mapping[str, Any]: Contains the information
        """
        #print(self.curr_delay)

        return {
            name_key         : self.weapon[0],
            ammo_key         : self.ammo,
            x_coordinate_key : self.coordinate.x,
            y_coordinate_key : self.coordinate.y,
        }

class Weapon:
    """
    Class of the weapon for the players
    """

    def __init__(self, 
                engine,
                name            : str, 
                maxAmmunition   : int, 
                latency         : int, 
                dmg             : int, 
                activated       : bool):
        """Constructor for creating a weapon

        Args:
            name (str): name of the weapon
            maxAmmunition (int): maximum of ammunitions the weapon can have
            latency (int): _description_
            dmg (int): _description_
            activated (bool): _description_
        """
        #print(F"Weapon: {self}")

        self.engine = engine

        self.name : str = name
    
        self.maxAmmunition  : int = maxAmmunition 

        self.currAmmunition : int = maxAmmunition if activated else 0

        #How much Frames does the Player have to wait for the next shot
        self.latency        : int = latency       if activated else float('inf')
        self.currLatency    : int = 0

        #How much damage does the Weapon cause
        self.damage         : int = dmg           if activated else 0 # safety reasons

        #---------------------------------
        # Statistics
        self.shotBullets    : int = 0
        self.hitTimes       : int = 0
        self.healthReduction: int = 0
        self.refilledAmmo   : int = 0
        self.kills          : int = 0

    def update(self):
        # reduce currLatency counter if needed
        if(self.currLatency > 0):

            # reduce the latency of the current weapon
            self.currLatency -= 1

class Map:
    """
    Class for handling the map
    It can read a map from strings array
    """

    def __init__        (self, 
                        engine,
                        name        : str,
                        width       : int, 
                        height      : int, 
                        map         : list[list[str]], 
                        mapString   : str, 
                        spawns      : dict[str:Spawn]):
        """Constructor for building a map.

        Args:
            width (int): the width of the map in blocks
            height (int): the height of the map in blocks
            map (list[list[str]]): the map in a list of a list. So that each block got a coordinate
            mapString (str): the map in wrapped in one string
            spawns (list[Spawn]): list of spawn objects, the map can have
            munitions (list[Munition]): list of munition objects, the map contains
        """
        
        # assign the engine for calculating
        self.engine                         = engine
        self.name       : str               = name
        self.width      : int               = width
        self.height     : int               = height
        self.map        : list[list[str]]   = map
        self.mapString  : str               = mapString
        self.spawns     : dict[Spawn]       = spawns
    
    def func            (spawns, x, y, char)    -> str:
        """helper function for handling the from list function

        Args:
            spawns (list[Spawn]): list of spawn objects
            x (_type_): the x-coordinate
            y (_type_): the y-coordinate
            char (_type_): the current char

        Returns:
            str: returns the char
        """
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
    
    def check_collision(self, 
                        coordinate  : Coordinate, 
                        object,  
                        tolerance   : float = 0) -> bool:        
        """Check if object collide with wall or munition. Algorithm is quite complicated (took a long time to evaluate). Checks in each direction if x or y is movable.
            If the next to a player is a spawn, lock the spawn
            if player collides with munition, increase the munition

        Args:
            coordinate (Coordinate): the coordinate on which the object wants to move
            object (Object): Either Bullet or Player
            dir (float, optional): Direction of the object in radians. Defaults to 0.
            tolerance (float, optional): How much distance to the real wall should be limited. Defaults to 0.25.

        Returns:
            bool: Did the Object hit the wall?
        """

        try:
            
            # Find char on next edge
            e_1 = self.map[round(coordinate.y - (self.engine.s.wall_hit_box + tolerance))][round(coordinate.x - (self.engine.s.wall_hit_box + tolerance))]
            e_2 = self.map[round(coordinate.y - (self.engine.s.wall_hit_box + tolerance))][round(coordinate.x - (self.engine.s.wall_hit_box - tolerance))]
            e_3 = self.map[round(coordinate.y - (self.engine.s.wall_hit_box - tolerance))][round(coordinate.x - (self.engine.s.wall_hit_box + tolerance))]
            e_4 = self.map[round(coordinate.y - (self.engine.s.wall_hit_box - tolerance))][round(coordinate.x - (self.engine.s.wall_hit_box - tolerance))] 

            # Check on what edge is a wall
            A = e_1 == "#"
            B = e_2 == "#"
            C = e_3 == "#"
            D = e_4 == "#"

            # if the object is a player
            if(type(object).__name__ == "Player"):

                #print(e_1,e_2,e_3,e_4)
                try:
                    self.engine.state.ammunitionPacks[int(e_1)].collected(player=object)
                except (KeyError, ValueError):
                    pass

                try:
                    self.engine.state.ammunitionPacks[e_2].collected(player=object)
                except (KeyError, ValueError):
                    pass

                try:
                    self.engine.state.ammunitionPacks[e_3].collected(player=object)
                except (KeyError, ValueError):
                    pass

                try:
                    self.engine.state.ammunitionPacks[e_4].collected(player=object)
                except (KeyError, ValueError):
                    pass

                # if the the next field is a spawn
                # Since spawns are marked with numbers, it is checked if 
                try:
                    self.spawns[e_1].use()
                except (KeyError, ValueError):
                    pass

                try:
                    self.spawns[e_2].use()
                except (KeyError, ValueError):
                    pass

                try:
                    self.spawns[e_3].use()
                except (KeyError, ValueError):
                    pass

                try:
                    self.spawns[e_4].use()
                except (KeyError, ValueError):
                    pass

                # Helper Booleans
                a =     A and not B and not C and not D
                b = not A and     B and not C and not D
                c = not A and not B and     C and not D
                d = not A and not B and not C and     D

                # In what direction is the object watching when it moves
                look_north_east = object.dirMove >  0          and object.dirMove <=  math.pi/2
                look_south_east = object.dirMove >   math.pi/2 and object.dirMove <=  math.pi
                look_north_west = object.dirMove <= 0          and object.dirMove >  -math.pi/2
                look_south_west = object.dirMove <= -math.pi/2 and object.dirMove >  -math.pi

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
    
    def render          (self)                  -> Mapping[str, Any]:
        """
        Returns relevant information about the map for the players

        Returns:
            Mapping[str, Any]: _description_
        """
        return {
            map_length_key : self.width,
            map_key        : self.mapString,
        }

class Player:
    """
    Class for handling Player's interaction, e.g. Shooting, Hitting, Dysing, Moving etc.
    """

    def __init__        (self, 
                        engine, 
                        playerName : str,
                        weapons : dict[list], 
                        speed : float,
                        rotation_speed : float, 
                        alive : int):

        # assign the engine to himself
        self.engine     = engine

        # Initiate the Username
        self.name : str = playerName

        self.alive : int = alive

        # Position is an Object of Coordinate
        self.currentPosition : Coordinate = Coordinate(0,0)

        # Represents the health
        self.health : int = 100

        # Represents the angle, in which the player is facing in radians
        self.dirView : float = 0
        self.dirMove : float = 10


        # Counts down from a specific number to zero for every tick, when it got activated
        self.justShot : int = -1

        # Counts down from a specific number to zero for every tick, when it got activated
        self.justHit : int = 0

        self.moveAnim : int = -1

        # Represents the current available weapons
        self.weapons : dict[Weapon] = {key : Weapon(self, *weapon) for key, weapon in weapons.items()}

        #Represents the current weapon
        #Current Weapon is the first in the dictionary
        self.currentWeaponIdx : int = 0
        self.currentWeapon : Weapon = None

        self.currentWeaponIdx, self.currentWeapon = [(key, weapon) for key, weapon in self.weapons.items() if weapon.currAmmunition != 0][0]

        # how many ticks does the player have to wait till he can shoot again
        self.changeWeaponDelay : int = 0

        '''
        Float describes how fast the Player is moving
        '''
        self.speed : float = speed

        '''Float describes how fast the Player is rotating'''
        self.rotation_speed : float = rotation_speed

        #------------------------------------------------
        #----------------Statistics----------------------
        
        # Represents score for kill and deaths
        self.kills                  : int = 0
        self.deaths                 : int = 0

        # kill/death rate
        self.killDeath              : float = 0
        self.selfHealthReduction    : int   = 0
        self.gotHitTimes            : int   = 0

        self.win                    : bool  = False

        #------------------------------------------------

        '''
        Integer how long player has to wait
        if -1 then Player is not participating in Game at all
        '''
        self.alive : int = 0

        '''
        Counts how many times a player did not send something in a row
        '''
        self.delayedTick : int = 0

    def find_spawn      (self, map : Map)                           -> bool:
        """
        Find an available Spawn for the Player
        Returns True if found
        Returns False if not found

        Args:
            map (Map): Map object to look for spawn

        Returns:
            bool: True if found and False if not found
        """

        #Did the Player find Spawn?
        flag = False

        #print(map.spawns)

        mapLen = len(map.spawns)

        rndIdx = random.randint(self.engine.s.spawn_index, mapLen + self.engine.s.spawn_index -1)

        for idx in range(mapLen):

            # Start from the rnd Spawn
            spawn = map.spawns[chr((idx + rndIdx) % mapLen + self.engine.s.spawn_index)]

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

        self.dirView = spawn.direction

        # Initiate the current position
        self.currentPosition = Coordinate(spawn.coordinate.x, spawn.coordinate.y)

        # Spawn was found
        return True

    def cond            (self)                                      -> bool:
        return self.name == "Picasso-Programmer"

    def shoot           (self)                               -> None:
        """
        Describes the function to be called when the player shoots
        A bullet with specific damage is then created
        
        Args:
            state (State): the current state of the game
        """
        
        weapon = self.currentWeapon

        if weapon.currAmmunition > 0 and weapon.currLatency == 0:

            #print(F"{self.name} just shot a bullet!")

            weapon.shotBullets += 1

            # The animation of shooting
            self.justShot =self.engine.s.shot_animation_modulo

            # Reduce the current ammo of current weapon by one
            weapon.currAmmunition -= 1

            # Start the delay of the weapon
            weapon.currLatency = weapon.latency

            dir = self.dirView

            # if the player is moving in that frame, reduce the accuracy
            if(self.moveAnim >= 0):

                rnd = random.uniform( -self.engine.s.accuracy_reduction, self.engine.s.accuracy_reduction)
                #print(rnd)
                dir += rnd

            # Add bullet to current state
            self.engine.state.bullets.append(
                Bullet(
                    self.engine,
                    # From whom was a bullet shot?
                    self,
                    #0.5 Blöcke vom Spieler entfernt entstehen die Bullets
                    self.currentPosition.x + self.engine.s.start_position_bullet * np.sin(self.dirView),
                    self.currentPosition.y + self.engine.s.start_position_bullet * np.cos(self.dirView),
                    #Shot in direction of player itself
                    dir
                )
            )
        else:
            #print(F"{self.name} has no bullets: {weaponA} or latency is still active : {weapon.curr_latency} ")
            pass

    def change_weapon   (self, idx : int)                           -> None:
        """
        Change the weapon by an indicator

        Args:
            idx (int): to what weapon should the player change
        """
                
        weaponDelay = round( self.engine.s.change_weapon_delay/ self.engine.s.tick_rate)

        print(F"Weapon was changed to: {idx}")

        # if the change came too often
        if(self.changeWeaponDelay >= weaponDelay - round( self.engine.s.change_weapon_invalid/ self.engine.s.tick_rate)):
            print("the change of weapon was too fast")
            return
        
        # if the idx is too high then modulo the length of the weapons
        self.currentWeaponIdx = idx % len(self.weapons)

        self.currentWeapon = self.weapons[self.currentWeaponIdx]

        # Reset the animation for bugs
        self.justShot          = -1

        # Wait 1 seconds to be able to shoot again
        self.changeWeaponDelay = weaponDelay
       
    def get_hit         (self, bullet : Bullet, mode : int)  -> None:
        """
        Describes the function to be called when the player is hit
        The health reduction is defined here and the happenings after getting killed

        Args:
            state (State): the current state of the game
            bullet (Bullet): the bullet which hits the player
            mode (int): in what game mode is the game
        """

        # The animation of getting hit shall go on for 1 second
        self.justHit = round( self.engine.s.hit_animation_duration/ self.engine.s.tick_rate)

        print(F"Player {self.name} is hit by player {bullet.player.name}")

        if(self.cond()):
            self.health -= round(bullet.weapon.damage/10)
        else:
            self.selfHealthReduction     += bullet.weapon.damage
            self.health                  -= bullet.weapon.damage
            self.gotHitTimes             += 1


            bullet.player.currentWeapon.healthReduction += bullet.weapon.damage
            bullet.player.currentWeapon.hitTimes        += 1
        
        # if player has died
        if(self.health < 1):

            # Synchronize the channel's information and send them to all participants
            async_to_sync(self.engine.channelLayer.group_send)(
                self.engine.lobbyName, 
                {
                "type": "game.event",
                state_key   : {
                    type_key    : event_key,
                    killer_key  : bullet.player.name,
                    dead_key    : self.name,
                    weapon_key  : bullet.player.currentWeapon.name, 
                },
                }
            )

            # increase score of player
            bullet.player.kills +=1
            bullet.player.currentWeapon.kills +=1

            # Update the kill/death rate
            try:
                bullet.player.killDeath = bullet.player.kills/bullet.player.deaths
            except ZeroDivisionError:
                bullet.player.killDeath = bullet.player.kills/1
            
            if(mode == 0):

                # Player is not alive anymore and waits till he respawns
                self.die()

            elif(mode == 1):
                
                # Player is not alive anymore
                self.remove_from_game(-1)
        
        #Remove bullet from State and delete the object
        try:
             self.engine.state.bullets.remove(bullet)
        except ValueError:
            print("Bullet already gone")

        # delete the object
        del(bullet)
            
    def move            (self, x : int = 0, y: int = 0)     -> None:
        """
        Validate the x and y directions and the move the player in the direction of the view plus his moves

        Args:
            state (State): The state about the current situation
            x (int, optional): From -1 to +1, if the player moves left or right. Defaults to 0.
            y (int, optional): From -1 to +1, if the player moves down or up. Defaults to 0.
        """

        #print(F"{self.name} is moving")

        too_close = False

        tmp = Coordinate(self.currentPosition.x, self.currentPosition.y)

        # Copy the direction of the players, so that it can be manipulated
        dir = self.dirView

        dir += math.atan2(x, y)

        if dir < 0:
            dir = (dir % -(2*math.pi)) 
            if dir < -math.pi:
                dir = dir % (math.pi + 0.00001)
        else:
            dir = (dir % (2*math.pi))
            if dir > math.pi:
                dir = dir % -(math.pi + 0.00001)

        self.dirMove = dir

        #print(F"1 tmp x: {tmp.x} y: {tmp.y}")

        #Move only in direction of max math.pi
        tmp.cod_move(self.speed, self.dirMove)

        #print(F"2 tmp x: {tmp.x} y: {tmp.y}")
        #print(F"obj x: {object.currentPosition.x} y: {object.currentPosition.y}")

        # Look for collision with other Players
        for player in self.engine.state.players:

            # if the on-going move is too close to another player then turn the boolean flag
            if(player.name != self.name and tmp.get_distance(player.currentPosition) < 1):
                
                print(F"Player {self.name} is too close to another player {player.name}")

                too_close = True

        # if player is not too close to an object
        if(not too_close):
            self.engine.state.map.check_collision(tmp, self, tolerance = self.engine.s.wall_hit_box_player_tolerance)
            self.moveAnim = (self.moveAnim + 1) % self.engine.s.move_animation_player_modulo # increase the value by one if he moves
        else:
            self.moveAnim = -1 # State for no movement

    def change_direction(self, mouseX : float)              -> None:
        """
        It changest the view direction of player if mouse is turning

        Args:
            mouseX (float): the degrees
        """

        dir = self.dirView + mouseX * self.rotation_speed

        if dir < 0:
            dir = (dir % -(2*math.pi)) 
            if dir < -math.pi:
                dir = dir % (math.pi + 0.00001)
        else:
            dir = (dir % (2*math.pi))
            if dir > math.pi:
                dir = dir % -(math.pi + 0.00001)

        self.dirView = dir
        
    def update          (self)                              -> None:
        """
        Reduce all latencies of the player by one if needed
        """

        # reduce justShot counter if needed
        if(self.justShot > 0):

            self.justShot -= round( self.engine.s.shot_animation_modulo/self.currentWeapon.latency)

            if (self.justShot <= 0):
                self.justShot = -1

        # reduce justHit counter if needed  
        if(self.justHit > 0):

            self.justHit  -= 1

        #if the self is currently changing its weapon
        if self.changeWeaponDelay > 0:

            #reduce the delay
            self.changeWeaponDelay -= 1

        if self.alive > 0:

            #reduce the waiting time
            self.alive -= 1

    def die             (self)                              -> None:
        """
        Describes the happening after dying
        """

        # increase the death variable
        self.deaths += 1

        # Update the kill/death rate
        try:
            self.killDeath = self.kills/self.deaths
        # if there is no death at all
        except ZeroDivisionError:
            self.killDeath = self.kills/1

        self.alive = round( self.engine.s.revive_waiting_time/ self.engine.s.tick_rate)

    def remove_from_game(self, value : int)                 -> None:
        """
        Remove the Player from the game without any waiting time

        Args:
            value (int, optional): _description_. Defaults to -1.
        """

        self.alive = value

    def render          (self)                              -> Mapping[str, Any]:
        """
        Returns all relevant information about the player for the Client

        Returns:
            Mapping[str, Any]: Returns the relevant information about the active player
        """
        
        return{
            x_coordinate_key        : self.currentPosition.x,
            y_coordinate_key        : self.currentPosition.y,
            health_key              : self.health,
            kills_key               : self.kills,
            death_key               : self.deaths,
            direction_view_key      : self.dirView,
            direction_move_key      : self.dirMove,
            justShot_animation      : self.justShot,
            justHit_animation       : self.justHit,
            move_animation_key      : self.moveAnim,
            weapon_change_animation : self.changeWeaponDelay,
            weapon_key              : self.currentWeaponIdx,
            ammo_key                : self.currentWeapon.currAmmunition,
        }

    def render_inactive (self)                              -> Mapping[str, Any]:
        """
        Returns all relevant information about the inactive player for the client


        Returns:
            Mapping[str, Any]: relevant informaiton about the inactivity
        """
        return{
            state_key : self.alive
        }

    def save_statistic  (self)                              -> None:
        """
        Saves the statistic of the player in the database
        with a timestamp

        Args:
            engine (Engine): the game itself
        """
        playerDB : StatisticDB = StatisticDB.objects.create(
            username        = self.name,
            lobby_name      = self.engine.lobbyName,
            game_mode       = self.engine.gameMode,
            map             = self.engine.state.map.name,
            players_count   = len(self.engine.playerQueue) + len(self.engine.state.players),
            won             = self.win,
            forbidden       = self.name in self.engine.playerForbidden,
            kills           = self.kills,
            deaths          = self.deaths,
            duration        = self.engine.tickNum * self.engine.s.tick_rate,
            finished        = self.engine.finished,
            disconnected    = self.alive == -2,
            shot_bullets    = sum([weapon.shotBullets       for weapon in self.weapons.values()]),
            hit_times       = sum([weapon.hitTimes          for weapon in self.weapons.values()]),
            health_reduction= sum([weapon.healthReduction   for weapon in self.weapons.values()]),
            refilled_ammo   = sum([weapon.refilledAmmo      for weapon in self.weapons.values()]),
            got_hit         = self.gotHitTimes,
            self_health_red = self.selfHealthReduction,
        )

        playerDB.save()

        for weapon in self.weapons.values():
            # Save the statistic about the weapon usage of the player

            weaponDB : WeaponStatistic = WeaponStatistic.objects.create(
                name            = weapon.name,
                player          = playerDB,
                shot_bullets    = weapon.shotBullets,
                hit_times       = weapon.hitTimes,
                health_reduction= weapon.healthReduction,
                refilled_ammo   = weapon.refilledAmmo,
            )
            weaponDB.save()

class State:
    """
    Class handling the current state of the game with just attribute
    """

    def __init__    (self, engine):
        self.engine                                     = engine
        self.map             : Map                      = None
        self.players         : list[Player]             = []
        self.bullets         : list[Bullet]             = []
        self.corpses         : dict[Player]             = []
        self.ammunitionPacks : dict[str:AmmunitionPack] = None

    def create_map  (self, mapDB : MapDB)           -> None:
        """Validates the input string to initialize an map object with list of spawns

        Args:
            mapDict (dict[str]): it contains the input string and the map length

        Returns:
            Map: Returns the map object
        """

        # saves all spawns from the map as spawn object
        spawns : dict[Spawn]= {}

        # saves all munition packs on the map as munition object
        ammunitionPacks : dict = {}

        char_count  : int = len(mapDB.string)

        width       : int = mapDB.len
        height      : int = char_count/mapDB.len

        inv_map     : str = mapDB.string.replace("#","").replace(".","").replace("W","").replace("S","").replace("N","").replace("E","").replace("M","")

        mapString   : str = mapDB.string

        if(len(inv_map) != 0):
            print(F"map contains invalid letters: >>>{inv_map}<<<<")

        # Look for spawns in the map
        for dir in [('N', math.pi), ('E', math.pi/2), ('S', 0), ('W', -math.pi/2)]:

            idx = 0

            # While the index did not reach the end
            while idx < char_count:

                # returns the position
                idx : int = mapString.find(dir[0])
                
                # if there was no spawn was found anymore
                if idx == -1:
                    break

                # create identic key
                char = chr(len(spawns) + self.engine.s.spawn_index)

                # replace the first name in the string with the spawn id as ascii
                mapString = mapString.replace(dir[0], str(char), 1)

                # get the coordinate of the spawn
                x = idx % width
                y = (idx - x)/width

                # create a spawn object and append it to the list of spawns
                spawns[char] = Spawn(
                        self.engine,
                        Coordinate(
                            x + 0.5,
                            y + 0.5,
                        ),
                        dir[1]   
                    )

        # start at the beginning to look for munition in the map
        idx = 0

        # While the index did not reach the end of the map string
        while idx < char_count:

            # returns the position of the char 'M'
            idx = mapString.find("M")

            # if nothing was found anymore
            if idx == -1:
                break

            # create identic key with negative integers
            char = chr(len(ammunitionPacks) + 150)

            # replace the first 'M' in the map string with the map id which differs from 
            mapString = mapString.replace('M', str(char), 1)

            # get the coordinate of the munition pack
            x = idx % width
            y = (idx - x)/width

            # create a munition object and append it to the list of munition packs
            ammunitionPacks[char] = AmmunitionPack(
                    self.engine,
                    Coordinate(
                        x + 0.5,
                        y + 0.5,
                    )
                )

        # Create as list of list for the map
        map = [list(mapString[sub-width:sub]) for sub in range(width, char_count + width, width) ]

        #[print(m) for m in map] 

        # if there are no spawns on the map          
        if(len(spawns) == 0):
            print("Map contains no spawn fields")

        self.map = Map(
            engine      = self.engine,
            name        = mapDB.name,
            width       = width,
            height      = height,
            map         = map,
            mapString   = mapDB.string,
            spawns      = spawns,
        )

        self.ammunitionPacks = ammunitionPacks

    def render      (self)                          -> Mapping[str, Any]:
        """
        Returns the relevant information about the for the clients to render

        Returns:
            Mapping[str, Any]: cotains the information
        """
        
        return { 
            player_key      : {p.name: p.render() for p in self.players},
            bullet_key      : [b.render() for b in self.bullets],
            corpses_key     : self.corpses,
            ammo_key        : [ammunitionPack.render() for ammunitionPack in self.ammunitionPacks.values() if ammunitionPack.curr_delay == 0],
            init_key  : {
                map_key         : self.map.render(),
                hit_anim_key    : round(self.engine.s.hit_animation_duration/self.engine.s.tick_rate),
                shot_anim_key   : self.engine.s.shot_animation_modulo,
                died_anim_key   : round(self.engine.s.died_animation_duration/self.engine.s.tick_rate),
                mov_b_anim_key  : self.engine.s.move_animation_bullet_modulo,
                mov_p_anim_key  : self.engine.s.move_animation_player_modulo,
            }
        }

class GameEngine(threading.Thread):
    """
    Thread for handling a game, in which the game loop runs

    Inherits:
        Class: threading.Thread
    """

    def __init__                    (self,
                                     setting            : SettingDB,
                                     lobbyName          : str, 
                                     map                : MapDB, 
                                     maxPlayers         : int,
                                     gameMode           : int, 
                                     winScore           : int, 
                                     endTime            : int,
                                     availableWeapons   : dict[int : list] = None, 
                                     ):
        """Defines the engine of the game. How the configuration is defined.

        Args:
            lobbyname (_type_): _description_
            mapString (_type_, optional): _description_. Defaults to None.
            maxPlayers (int, optional): _description_. Defaults to 6.
            gameMode (int, optional): _description_. Defaults to 0.
            winScore (int, optional): _description_. Defaults to 20.
            endTime (int, optional): _description_. Defaults to MAX_ENDTIME.
            availableWeapons (dict, optional): _description_. Defaults to AVAILABLE_WEAPONS.
        """

        # Get the current settings
        self.s : SettingDB = setting

        # get all available weapons
        self.available_weapons = {        
            weapon.index: [
            weapon.name,
            weapon.ammunition,
            round(weapon.latency/ self.s.tick_rate),
            weapon.damage,
            True, #TODO: Activated
            ] for weapon in WeaponDB.objects.all()
        }

        # Did the game started?
        self.startFlag = False

        # Should the game stop?
        self.stopFlag = False

        #game_modes
        # 0: Play until one player has enough kills. Revive after 10 Seconds
        # 1: Last man standing, no reviving at all
        self.gameMode = gameMode

        # Has the game finished till the time stopped or somebody finished the condition
        self.finished : bool = False

        #print(F"Initializing GameEngine: {lobbyname} with players: {playersName}")
        
        # give the available weapons as a restriction
        # TODO: Noch bearbeiten, wenn Waffen in Lobby wählbar sind
        self.weapons = self.available_weapons

        # Create a thread to run the game
        super(GameEngine, self).__init__(daemon = True, name = "GameEngine")

        # the times of total ticks
        self.tickNum = 0

        # random ID for the game
        self.name = uuid.uuid4()

        # lobbyName for communication
        self.lobbyName = lobbyName

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

        #Forbidden Player: Players who were once in the game but then left permanently
        self.playerForbidden : list[str] = []

        #How man players are allowed in the game
        self.maxPlayers = maxPlayers

        # defines the state of the game
        self.state = State(self)

        self.state.create_map(map)

    def run                         (self)                                      -> None:
        """
        Contains the infinite loop in which the tick rate is defined
        It can stop the loop
        """

        # infinite loop
        while True:

            if(self.startFlag):

                start = time.time()

                # After each tick update the current status of the game
                self.tick()

                # Broadcast the current Status to all players in game
                self.broadcast_state()

                # Sleep for a specific time, in which the game will calculate every new status
                try:
                    time.sleep( self.s.tick_rate - (time.time() - start))
                except ValueError:
                    # indication for not computing fast enough to reach the Tick-Rate
                    #print("1", end="")
                    pass

            elif(self.stopFlag):
                # if the worker wants to stop the thread
                # save all player's statistic 
                for player in self.playerQueue + self.state.players :
                    player.save_statistic()

                break

    def broadcast_state             (self)                                      -> None: 
        """
        The broadcast method which broadcast the current game state to the PlayerConsumers in the channel
        """

        # Get the current information about the game state
        stateJson = self.state.render()

        #print(stateJson)

        stateJson[inactive_key] = {player.name : player.render_inactive() for player in self.playerQueue}

        # Synchronize the channel's information and send them to all participants
        async_to_sync(self.channelLayer.group_send)(
            self.lobbyName, 
            {
             "type": "game.update",
             state_key   : stateJson
            }
        )

    def tick                        (self)                                      -> None:
        """ 
        Function in which every tick is described. It contains the 
        """

        # increase the ticknum
        self.tickNum += 1         

        # if time limit was reached
        if(self.tickNum >= self.endTime):
            
            self.finish_game()

        begin = time.time()

        with self.eventLock:
            events = self.eventChanges.copy()
            self.eventChanges.clear()

        end = time.time()

        eventLock = end - begin
        #print(F"event: {end-start}s\n")

        if self.state.players:
            self.process_players(events)

        start = time.time()

        #print(F"players: {start-end}s\n")
        processPlayers = start-end

        if self.state.bullets:
            self.process_bullets()
        
        end = time.time()

        #print(F"bullets: {end-start}s\n")
        bullets = end-start
        
        self.process_hits()

        if self.state.corpses:
            self.process_corpses()
        
        start = time.time()

        #print(F"hits: {start-end}s\n")
        processHits = start - end
        
        self.process_new_players()

        end = time.time()

        #print(F"new players: {end-start}s\n")
        newPlayer = end - start

        self.process_spawns()

        finish = time.time()

        self.process_ammunitionPack()

        spawns = finish - end
        #print(F"spawns: {start-end}s\n\n")
        if(finish-begin >= self.s.tick_rate):
            print(F'''
                eventLock {eventLock}
                processPlayers {processPlayers}
                bullets {bullets}
                processHits {processHits}
                newPlayer {newPlayer}
                spawns {spawns}
            ''')

    def process_players             (self, events : dict)                       -> None:
        """
        Handle the actions of a player and check the winning conditions
        Every input of a player is validated in here

        Args:
            events (dict): contains player's input
        """

        # if game is about last man standing and only one Player remained
        if self.gameMode == 1 and len(self.state.players) == 1:

            print(F"Last Man Standing was won because only one player {self.state.players[0].name} left")
            
            # Declare the winner
            self.state.players[0].win = True
            
            # Declare it as a win
            self.win()

        for idx, player in enumerate(self.state.players):

            #if player did not respond for one second or more
            if player.delayedTick >= round( self.s.player_delay_tolerance/ self.s.tick_rate):

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
        
                print(F"{player.name} was added to the corpses")

                self.state.corpses.append(
                    {
                        player_key       : player.name, 
                        x_coordinate_key : player.currentPosition.x, 
                        y_coordinate_key : player.currentPosition.y, 
                        duration_key     : round( self.s.died_animation_duration/ self.s.tick_rate),
                    }) 

            # if the player was removed permanently
            elif player.alive == -1:

                # remove it from the players
                self.state.players.pop(idx)
                
                print(F"{player.name} was added to the corpses")

                # append the player to the corpses
                self.state.corpses.append(
                    {
                        player_key       : player.name, 
                        x_coordinate_key : player.currentPosition.x, 
                        y_coordinate_key : player.currentPosition.y, 
                        duration_key     : round( self.s.died_animation_duration/ self.s.tick_rate),
                    }) 

            # if the gamemode is about killing enough player and enough player were killed, then declare the game won
            if self.gameMode == 0 and player.kills >= self.winScore:
                
                print(F"Enough player were killed by {player.name}")
                
                # Declare the player as winner
                player.win = True

                # End the game
                self.win()
                
            #print(events.keys())

            if player.name in events.keys():

                #print(F"Process players {self.state.players} with {events}")

                event = events[player.name]

                # change player's direction
                player.change_direction(event[mouseDelta_key])

                # If the player wants to change the weapon                
                if(event[weapon_key] != player.currentWeaponIdx):

                    player.change_weapon(event[weapon_key])

                weapon = player.currentWeapon

                # if the player did not respond for more than one time
                if(player.delayedTick > 1):
                    #print(F"Player {player.name} did not respond for {player.delayedTick} ticks")

                    #reset the delayedTick
                    player.delayedTick = 0

                # reduce the weapons latency by one
                weapon.update()
                
                # reduce the latencies of the player by one
                player.update()

                if(event[x_coordinate_key] != 0 or event[y_coordinate_key] != 0):
                    player.move(event[x_coordinate_key], event[y_coordinate_key])
                    #print(F"x: {player.currentPosition.x}, y: {player.currentPosition.y}")
                else:
                    # set the direction of movement to the default value
                    player.dirMove  = 10

                    # set the movement animation index to default
                    player.moveAnim = -1

                # if the player has clicked the mouse button
                if(event[click_key]):

                    # if the weapon is ready to shoot
                    if(player.changeWeaponDelay == 0):

                        # let the player shoot
                        player.shoot()

                    else:
                        #print("Weapon delay")
                        pass
            elif(player.alive == 0):
                #Increase the delayed tick of the player
                player.delayedTick += 1
                        
    def process_hits                (self)                                      -> None:
        """
        Checks if any bullet hits a player
        """

        [player.get_hit(bullet, self.gameMode) 
            for player in self.state.players 
                for bullet in self.state.bullets 
                    if bullet.currentPosition.get_distance(player.currentPosition) < self.s.hit_box or
                       bullet.middlePosition.get_distance(player.currentPosition)  < self.s.hit_box]

    def process_bullets             (self)                                      -> None:
        """
        Checks if bullet hits the wall
        """

        # Filter out every bullet which hit the wall to delete the objects and remove them from the current list
        [self.state.bullets.pop(idx) 
            for idx, bullet in enumerate(self.state.bullets) 
                if bullet.update_pos()].clear()

    def process_corpses             (self)                                      -> None: 
        """
        Process the current Corpses on the battlefield
        """

        # reduce corpse remaining time and if needed remove it
        for corpse in self.state.corpses:

            # if remaining time is finished
            if(corpse[duration_key] == 0):
                self.state.corpses.remove(corpse)

            # reduce the duration by one
            corpse[duration_key] -= 1 

    def process_spawns              (self)                                      -> None:
        """
        Reduce the tick of every Spawn, so new Player can join
        None will be returned
        """

        [spawn.update() for spawn in self.state.map.spawns.values()]

    def apply_events                (self, player: str, events : dict[str:Any]) -> None:
        """
        Transfer the changes from the GameConsumer to the GameEngine
        """
        
        with self.eventLock:
            self.eventChanges[player] = events

    def join_game                   (self, playerName: str)                     -> None:
        """
        When a player wants to join the game then evaluate it here

        Args:
            playerName (str): the name of the player
        """

        stateP = next((obj for obj in self.state.players if obj.name == playerName), False)
        stateQ = next((obj for obj in self.playerQueue if obj.name == playerName),False)

        # Look if player is already in the game
        if(stateP):
            if(stateP.delayedTick < 30):

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
                stateQ.alive = round( self.s.player_not_responding_time/ self.s.tick_rate)
        except:

            # if the Player joins the game for the first time
            with self.playerLock:

                # Append Player to the queue so it can be appended to the game
                self.playerQueue.append(Player(self, 
                                                playerName      = playerName, 
                                                alive           = 0,
                                                weapons         = self.weapons,
                                                speed           = self.s.player_speed,
                                                rotation_speed  = self.s.rotation_speed,       
                                                ))

                # TODO: Bedingung für den Start des Spiels ändern
                # if the game has not been started yet and enough player have joined the game
                if(not self.startFlag and len(self.playerQueue) > 0):
                    
                    # start the game
                    self.startFlag = True

    def process_new_players         (self)                                      -> None:
        """
        Look if new Players should join the game
        """

        #Pointer on the queues list
        idx = 0

        # Amount of players who are disconnected
        disconnect = 0

        #print(self.playerQueue)

        for player in self.playerQueue:

            # if player is ready to spawn on the battle
            if(player.alive == 0):

                print(F"{player.name} is spawning the game")

                #if spawn is found returns true
                if not player.find_spawn(self.state.map):

                    print("No spawn was found yet")

                    #Wait for specific time if player could not spawn
                    player.alive = round( self.s.player_occupied_spawn_time/ self.s.tick_rate)

                #set his health back to 100
                player.health = 100

                # reset the delayed tick of the rejoined player
                player.delayedTick = 0

                # add the players to the game
                self.state.players.append(self.playerQueue.pop(idx))

            # if player is waiting for rejoining
            # -1 Players are not included
            elif player.alive > 0:

                #reduce wait time of player
                player.alive -= 1

                #skip Player for pop() method
                idx += 1
            elif player.alive == -2:

                disconnect += 1

                #skip Player for pop() method
                idx += 1 
            else:
                idx += 1

        if(disconnect > 0 and not self.state.players and disconnect == len(self.playerQueue)):
            print(F"Lobby will be closed since nobody connected in game")
            
            # Stop doing somethin
            self.startFlag = False
            
            # Send the essential information for validate the winner of the game
            async_to_sync(self.channelLayer.send)(
                "game_engine", 
               {
                "type"    : "close.game",
                group_key   : self.lobbyName,
                }
            ) 

    def process_ammunitionPack      (self)                                      -> None:
        """
        Process the ammunitionPacks current 
        """
        
        [ammunitionPack.update() for ammunitionPack in self.state.ammunitionPacks.values()]
                
    def win                         (self)                                      -> None:
        """
        Is called if the game is finished.

        Args:
            winningPlayers (list[Player]): list of winning player
        """

        # the game finished completely
        self.finished = True

        # Stop doing something
        self.startFlag = False

        # Send the essential information for validate the winner of the game
        async_to_sync(self.channelLayer.send)(
            "game_engine", 
            {
             "type"     : "win",
             time_key   : self.tickNum * self.s.tick_rate,
             group_key  : self.lobbyName, 
             player_key : 
             [
                 { 
                   name_key       : p.name,
                   kills_key      : p.kills,
                   death_key      : p.deaths,
                   killDeath_key  : p.killDeath,
                   win_key        : p.win
                 } 
                   for p in self.state.players] +
             [   
                 { 
                   name_key       : p.name,
                   kills_key      : p.kills,
                   death_key      : p.deaths,
                   killDeath_key  : p.killDeath,
                   win_key        : p.win
                 } 
                   for p in self.playerQueue]
            }
        )

    def finish_game                 (self)                                      -> None: 
        '''
            When the time has reached its limit
        '''
        print("the time limit has been reached")

        # if the winner is about the highest kills
        if self.gameMode == 0:

            # Get the best players out of all players and broadcast them
            self.look_for_best_players(self.state.players + self.playerQueue)
            
            # Broadcast the finished state
            self.win()
        
        elif self.gameMode == 1:

            # Get the best players out of still alive players and broadcast them
            self.look_for_best_players(self.state.players)
            self.win()

    def look_for_best_players       (self, players : list[Player])              -> None:
        
        # Look for the highest kills in queue and in current game
        highest_kills = max(players, key=attrgetter('kills')).kills

        # Look for all Players with highest kills
        bestPlayers = [player for player in players if player.kills == highest_kills]

        # if there is only one Player the best player
        if len(bestPlayers) == 1:

            # return instantly because there is already an unambigous best player
            bestPlayers[0].win = True

        else:

            # Look for the highest kills in queue and in current game
            highestKillDeath = max(bestPlayers, key=attrgetter('killDeath')).killDeath

            # Look for all Players with highest kills
            for player in bestPlayers:
                if player.killDeath == highestKillDeath:
                    player.win = True   