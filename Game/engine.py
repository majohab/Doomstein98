import logging
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
        self.lock_time = 5/tick_rate

    def update_occupation(self):
        '''
        Update the status of a spawn
        > -1 means Player is using the Spawn
        '''

        if self.lock_time == 1:
            print(F"Spawn at x: {self.coordinate.x} y: {self.coordinate.y} is free again")

        if(self.lock_time > 0):
            self.lock_time -= 1

class Weapon:

    def __init__(self, max_ammunition : int, latency : int, dmg : int):

        self.max_ammunition = max_ammunition

        self.curr_ammunition = max_ammunition

        #How much Frames does the Player have to wait for the next shot
        self.latency = latency
        self.curr_latency = 0

        #How much damage does the Weapon cause
        self.damage = dmg

# List for all available weapons
AVAILABLE_WEAPONS = {
    "P99" : Weapon(
        50,             #50 Kugeln in der Waffe
        0.8/tick_rate,  #Jede 0.8 Sekunden kann geschossen werden
        20              # The weapon reduces 20 health per bullet
    ),
    "MP5" : Weapon(
        200,            #200 Kugeln in der Waffe
        0.1/tick_rate,  #Jede 0.1 Sekunden kann geschossen werden   
        10              # The Weapon reduces 10 Health per Bullet 
    ),
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
    
    # validate the input string of map
    # Static Method
    def from_list(strings: list):

        spawns = list()

        map = pd.DataFrame([list(string) for string in strings])
        
        for idx_s, string in enumerate(strings):
            
            if len(string.replace('#','').replace('.','').replace('N','').replace('E','').replace('S','').replace('W','')) != 0:
                print('Map contains invalid values. It only accepts \"#\" or \".\" and spawn fields')

                        #Check if Map fits the format
            if len(string) != len(strings[-1]):
                print("Map is invalid")

            #Handling for spawns
            for idx_c, char in enumerate(string):

                #Check if the direction fits to the coordinate
                # N and S are reversed, so N gets math.pi
                if(char == 'N' and strings[idx_s-1][idx_c] == '.'):
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
                # N and S are reversed, so S gets 0
                if(char == 'S' and strings[idx_s+1][idx_c] == '.'):
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
            map,
            strings,
            spawns,
        )

    # Check if Object collides with Map
    # Returns True if Oject collide with wall in any way
    def check_collision(self, coordinate : Coordinate, object, tolerance : float = 0.25) -> int:        
        '''
        Checks collision for players and bullets. Tolerance is for bullet only
        '''

        # check collision in for fields around the object
        collision = False

        #try:
        A = self.map.iloc[round(coordinate.y - (0.5 + tolerance)),round(coordinate.x - (0.5 + tolerance))] == "#"
        B = self.map.iloc[round(coordinate.y - (0.5 + tolerance)),round(coordinate.x - (0.5 - tolerance))] == "#"
        C = self.map.iloc[round(coordinate.y - (0.5 - tolerance)),round(coordinate.x - (0.5 + tolerance))] == "#"
        D = self.map.iloc[round(coordinate.y - (0.5 - tolerance)),round(coordinate.x - (0.5 - tolerance))] == "#"

        A_l = self.map.iloc[round(coordinate.y - 0.57),round(coordinate.x - 0.57)] == "#"
        B_l = self.map.iloc[round(coordinate.y - 0.57),round(coordinate.x - 0.43)] == "#"
        C_l = self.map.iloc[round(coordinate.y - 0.43),round(coordinate.x - 0.57)] == "#"
        D_l = self.map.iloc[round(coordinate.y - 0.43),round(coordinate.x - 0.43)] == "#"

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

        #print(north)
        #print(east)
        #print(south)
        #print(west)

        ne = A and B and D  or     A_l and not B_l and not C_l and not D_l
        se = B and C and D  or not A_l and     B_l and not C_l and not D_l
        sw = A and C and D  or not A_l and not B_l and     C_l and not D_l
        nw = A and B and C  or not A_l and not B_l and not C_l and     D_l     

        # If Player is in corner, dont change anything
        if ne or se or sw or nw:
            print(F"Player is located at a corner: y: {coordinate.y} x: {coordinate.x}")
            return True

        # if Player is not located at east nor west wall
        if not (west or east):
            object.current_position.x = coordinate.x
        else:
            print()
            collision = True
        
    
        # if Player is not located at north nor south wall
        if not (north or south):
            object.current_position.y = coordinate.y
        else:
            collision = True
        
        return collision

    #except IndexError:
     #       print(F"Bewegung nach x:{coordinate.x} und y:{coordinate.y} war ungültig und wurde zurückgesetzt!")
      #      object.current_position = Coordinate(3.5,3.5)
       #     return True
        
    def render(self) -> Mapping[str, Any]:
        return self.map_string

class Player:
    '''
    Class for handling players
    '''

    # Initiate player
    def __init__(self, username : str, position : Coordinate = Coordinate(3.5,3.5), weapons: list[Weapon] = {"P99" : AVAILABLE_WEAPONS["P99"], "MP5" : AVAILABLE_WEAPONS["MP5"]}, speed : float = tick_rate/0.1, rotation_speed : float = tick_rate/1, alive : int = 0):
        
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
        self.weapons = weapons

        #Represents the current weapon
        #Current Weapon
        self.current_weapon = weapons["P99"] 

        self.change_weapon_delay = 0

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

    def find_spawn(self, map):
        '''
        Find an available Spawn for the Player
        Returns True if found
        Returns False if not found
        '''
        #Did the Player find Spawn?
        flag = False

        map_len = len(map.spawns)

        rnd_idx = random.randint(0,map_len-1)

        for idx in range(map_len):

            # Start from the rnd Spawn
            spawn = map.spawns[(idx+rnd_idx)%map_len]

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
        self.current_position = spawn.coordinate
        # Spawn was found
        return True

    def shoot(self, state):
        '''
        Describes the function to be called when the player shoots
        '''
        
        weapon = self.current_weapon

        if weapon.curr_ammunition > 0 and weapon.curr_latency == 0:

            print(F"{self.name} just shot a bullet!")

            speed = 0.5

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

    def change_weapon(self, weapon : str):
        '''
        Change the weapon by an indicator
        '''
        #TODO: Ausführen: Was soll genau passieren
        # Was gibt es für Übergabeparameter
        try:
            self.current_weapon = self.weapons[weapon]
            # Wait 1 seconds to be able to shoot again
            self.change_weapon_delay = 1/tick_rate
        except KeyError:
            print(F"Die Waffe {weapon} gibt es nicht im Repetoire")

    #Describes the function to be called when the player is hit
    def get_hit(self, shooting_player, mode):

        # The animation of getting shot shall go on for 1 second
        self.justShot = 1/tick_rate

        print(F"Player {self.name} is hit by player {shooting_player.name}")

        self.health -= shooting_player.current_weapon.damage
        
        if(self.health < 1):
            if(mode == 0):

                # increase score of player
                shooting_player.kills +=1

                # Update the kill/death rate
                try:
                    shooting_player.kill_death = shooting_player.kills/shooting_player.deaths
                except ZeroDivisionError:
                    shooting_player.kill_death = shooting_player.kills/1

                # Player is not alive anymore and waits till he respawns
                self.die()
            elif(mode == 1):
                # Player is not alive anymore
                self.remove_from_game()

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

        #TODO: Anpassen im Moment 10 Sekunden warten
        self.alive = 10/tick_rate

    def remove_from_game(self):

        self.alive = -1

    '''
    Returns all relevant information about the Player for the Client
    '''
    def render(self) -> Mapping[str, Any]:
        return{
            "x"           : self.current_position.x,
            "y"           : self.current_position.y,
            "h"           : self.health,
            "dir"         : self.direction,
            "shot_an"     : self.justShot,
            "hit_an"      : self.justHit,
            "cha_weap_an" : self.change_weapon_delay,
            "ammo"        : self.current_weapon.curr_ammunition,
            "alive"       : self.alive,
        }


class Bullet:
    '''
    Creating and handling Bullets
    '''

    # Initiate bullet
    def __init__(self, origin_player : Player, origin_pos : Coordinate, direction : float):

        print("A bullet has been created")

        self.player           : Player     = origin_player
        self.origin_pos       : Coordinate = origin_pos
        self.current_position : Coordinate = origin_pos

        self.direction : float = direction

        # One Movement per frame
        self.speed : float = 0.1 #TODO: Anpassen

    # Execute for every bullet this function
    # Returns True if bullet collide with Wall or Player
    def update_pos(self, map : Map):

        tmp = Coordinate(self.current_position.x,self.current_position.y)

        tmp.cod_move(self.speed, self.direction)

        # Check collision with Wall
        if map.check_collision(tmp, self, 0.05):
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
        self.players = []#[Player(name, ) for name in players_name]
        self.bullets = bullets


    def render(self) -> Mapping[str, Any]:
        return { 
            "map" :     self.map.render(),
            "players" : {p.name: p.render() for p in self.players},
            "bullets" : [b.render() for b in self.bullets]
        }

# Create a thread to run it indefinitely
class GameEngine(threading.Thread):

    # Constructor function for GameEngine
    def __init__(self, group_name, players_name : list[str] = [], map_string = MAPS[0], max_players : int = 6, game_mode : int = 0, win_score : int = 20, end_time : int = (30*60)/tick_rate):
        
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

        print(F"Starting engine loop with self.running: {self.running}")

        # infinite loop
        while self.running:

            if self.start_flag:

                # After each tick update the current status of the game
                self.tick()

                # Broadcast the current Status to all players in game
                self.broadcast_state()

                # Sleep for a specific time, in which the game will calculate every new status
                time.sleep(tick_rate)


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
            if player.delayed_tick >= 1/tick_rate:

                #TODO: What happens if the User does not respond
                        #He has to wait for 10 seconds

                player.alive = 10/tick_rate

                print(F"Player {player.name} did not respond for one second or more! So he was removed from GameEngine!")

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
                
            if player.name in events.keys():

                
                if(player.delayed_tick > 1):
                    print(F"Player {player.name} did not respond for {player.delayed_tick} ticks")

                #reset the delayed_tick
                player.delayed_tick = 0

                weapon = player.current_weapon

                if(weapon.curr_latency > 0):
                    # reduce the latency of the current weapon
                    weapon.curr_latency -= 1
                
                event = events[player.name]

                player.change_direction(event["mouseDeltaX"])

                if(event["x"] != 0 or event["y"] != 0):
                    player.move(self.state, event["x"], event["y"])

                if(event["leftClick"] and player.change_weapon_delay == 0):
                   player.shoot(self.state)
            else:
                #Increase the delayed tick of the player
                player.delayed_tick += 1
            
            #if the player is currently changing its weapon
            if player.change_weapon_delay > 0:

                #reduce the delay
                player.change_weapon_delay -= 1
            
    def process_hits(self) -> None:
        '''
        Checks if any bullet hits a player
        '''

        [player.get_hit(bullet.player, self.game_mode)  for player in self.state.players for bullet in self.state.bullets if bullet.current_position.get_distance(player.current_position) < 0.1]

        #for player in self.state.players:

        #    for bullet in self.state.bullets: 

                # If the bullet is too close to the player, then recognize it as a collision
       #         if bullet.current_position.get_distance(player.current_position) < 0.1:

                    
#                    break

    def process_bullets(self) -> None:
        '''
        Checks if bullet hits the wall
        '''
        # Make the next move for all bullets
        # if True then it collide with Wall or Player, so remove it
        self.state.bullets = [bullet for bullet in self.state.bullets if not bullet.update_pos(self.state.map)]

    def process_spawns(self) -> None:
        '''
        Reduce the tick of every Spawn, so new Player can join
        None will be returned
        '''
        [spawn.update_occupation() for spawn in self.state.map.spawns]


    def apply_events(self, player: str, events) -> None:
        '''
        Transfer the changes from the GameConsumer to the GameEngine
        '''

        #print("Applying changes for " + player)
        
        with self.event_lock:
            self.event_changes[player] = events

    def join_game(self, player_name: str) -> None:

        print(F"\n\nPlayer {player_name} joined game!\n\n", )

        # Look if player is already in the game
        if not next((obj for obj in self.state.players if obj.name == player_name), None) is None:

            print(F"\n\nPlayer {player_name} is already in game!\n")
            return
        
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

            if(player.alive == 0):

                #if spawn is found returns true
                if not player.find_spawn(self.state.map):

                    print("No spawn was found yet")

                    #Wait for another 0.1 second
                    player.alive = 0.1/tick_rate

                #set his health back to 100
                player.health = 100

                # add the players to the game
                self.state.players.append(self.player_queue.pop(idx))

                print(player.name)
            # if player is waiting for rejoining
            # -1 Players are not included
            elif player.alive > 0:

                #reduce wait time of player
                player.alive -= 1

                #skip Player for pop() method
                idx += 1
            else:
                #skip Player for pop() method
                idx += 1   

    def win(self, winning_players : list[Player]) -> None:

        print(F"{winning_players} wins the game")

        # Send the essential information for validate the winner of the game
        async_to_sync(self.channel_layer.send)(
            "game_engine", 
            {
             "type"    : "win",
             "time"    : self.tick_num * tick_rate,
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







                
        
        



