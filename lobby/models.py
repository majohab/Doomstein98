from django.db import models
import django.core.validators as validator

MAX_PLAYERS = 10

# Create your models here.
    
class Map(models.Model):
    """ Map model containing the map data

    Inherits:
        models (Class): Base model class

    Returns:
        Map: Map object
    """
    name = models.CharField(max_length=50, unique=True)
    string = models.CharField(max_length=10000, unique=True)
    len = models.SmallIntegerField(default=0)
    description = models.CharField(max_length=200)

    def __str__(self) -> str:
        """ Prints user data

        Returns:
            str: Map name
        """
        return self.name

class Weapon(models.Model):
    """ Weapon model containing the data of a weapon

    Inherits:
        models (Class): Base model class

    Returns:
        Weapon: Weapon object
    """
    index       = models.PositiveSmallIntegerField      (default=0, unique=True)
    name        = models.CharField                      (max_length=50, unique=True)
    ammunition  = models.PositiveSmallIntegerField      (default=30,  validators=[validator.MinValueValidator(1, 'The Weapon has to have at least 1 bullet')])
    latency     = models.FloatField                     (default=0.1, validators=[validator.MinValueValidator(0.01),validator.MaxValueValidator(10)]) # in sec
    damage      = models.PositiveSmallIntegerField      (default=20,  validators=[validator.MinValueValidator(1, "The Weapon has to do at least one damage")])

    def __str__(self) -> str:
        """ Prints user data

        Returns:
            str: Weapon name
        """
        return self.name

class Lobby(models.Model):
    """ Lobby model containing the lobby data

    Args:
        models (Class): Base model class

    Returns:
        Lobby: Lobby object
    """
    name            = models.CharField                  (max_length=50, unique=True, validators=[validator.RegexValidator(regex='([^ \n])+', message="No spaces")]) # Regex checks if there are empty spaces in the name
    map             = models.ForeignKey                 (Map, on_delete=models.CASCADE)
    mode            = models.PositiveSmallIntegerField  (default=0)
    max_players     = models.PositiveSmallIntegerField  (default=4, validators=[validator.MinValueValidator(2,"To play reasonably, you should play at least with two player"), validator.MaxValueValidator(MAX_PLAYERS, "The Server can not handle more players")])
    current_players = models.PositiveSmallIntegerField  (default=0, validators=[validator.MaxValueValidator(max_players)])
    game_runtime    = models.PositiveSmallIntegerField  (default=10,validators=[validator.MinValueValidator(2), validator.MaxValueValidator(60)])

    def __str__(self) -> str:
        """ Prints user data

        Returns:
            str: Lobby name
        """
        return self.name

class Statistic(models.Model):
    """
    Contains every important statistic concerning the user

    Args:
        models (_type_): _description_
    """
    time            = models.DateTimeField              (unique=True, auto_now_add=True)

    username        = models.CharField                  (max_length=50)
    lobby_name      = models.CharField                  (max_length=50)
    game_mode       = models.SmallIntegerField          (default=0)
    map             = models.CharField                  (max_length=50)
    players_count   = models.SmallIntegerField          (default=0)
    
    won             = models.BooleanField               ()
    forbidden       = models.BooleanField               ()

    kills           = models.SmallIntegerField          (default=0)
    # kills with weapons
    deaths          = models.SmallIntegerField          (default=0)
    # died by weapon
    
    duration        = models.SmallIntegerField          (default=0)

    finished        = models.BooleanField               ()
    disconnected    = models.BooleanField               ()

    shot_bullets    = models.SmallIntegerField          (default=0)
    hit_times       = models.SmallIntegerField          (default=0)
    health_reduction= models.SmallIntegerField          (default=0)

    # How many bullets were refilled
    refilled_ammo   = models.SmallIntegerField          (default=0)

    got_hit         = models.SmallIntegerField          (default=0)
    self_health_red = models.SmallIntegerField          (default=0)

class WeaponStatistic(models.Model):
    """
    Contains statistic to the weapon related to the user

    Args:
        models (_type_): _description_
    """
    time            = models.DateTimeField              (auto_now_add=True)

    name            = models.CharField                  (max_length=255)
    player          = models.ForeignKey                 (Statistic, on_delete=models.CASCADE)
    shot_bullets    = models.SmallIntegerField          (default=0)
    hit_times       = models.SmallIntegerField          (default=0)
    kills           = models.SmallIntegerField          (default=0)
    health_reduction= models.SmallIntegerField          (default=0)
    refilled_ammo   = models.SmallIntegerField          (default=0)

class Setting(models.Model):
    """
    Settings for the constants, which are configurations for the game

    Args:
        models (_type_): _description_
    """

    index                           = models.SmallIntegerField(default=0, unique=True)
    
    tick_rate                       = models.FloatField(default=1/60) 
    
    # Get calculated as divisor
    # TICK_RATE/value
    player_speed                    = models.FloatField(default=0.1,  help_text="Get calculated as divisor")
    rotation_speed                  = models.FloatField(default=1,    help_text="Get calculated as divisor")
    bullet_speed                    = models.FloatField(default=1/60, help_text="Get calculated as divisor")

    # The minimum/maximum range of ammunition in a munition package in percentage of max ammunition of a weapon
    min_munition                    = models.FloatField(default=0.2,  help_text="The minimum percentage of ammunition calculating randomly in a munition package of a weapon")
    max_munition                    = models.FloatField(default=1  ,  help_text="The maximum percentage of ammunition calculating randomly in a munition package of a weapon")
    step_munition                   = models.FloatField(default=0.2,  help_text="The steps between min and max ammunition calculating randomly in a munition package of a weapon") 
    default_ammunition_delay        = models.FloatField(default=2,    help_text= "The delay in minutes till the ammunition is respawned")

    # Start Indizes
    spawn_index                     = models.SmallIntegerField(default=50, help_text="The starting index for handling spawns. It should be at least as high")

    shot_animation_modulo           = models.SmallIntegerField(default=100, help_text="How many Frames are needed to display an animation for shooting")
    move_animation_bullet_modulo    = models.SmallIntegerField(default=100, help_text="How many Frames are needed to display an animation for moving a player")
    move_animation_player_modulo    = models.SmallIntegerField(default=100, help_text="How many Frames are needed to display an animation for moving a bullet")

    #TODO: SHould be edited
    hit_animation_duration          = models.SmallIntegerField(default=1,  help_text="How many seconds are needed to display an animation for dying")         
    died_animation_duration         = models.SmallIntegerField(default=10, help_text="How many seconds are needed to display an animation for getting hit")

    change_weapon_delay             = models.SmallIntegerField(default=1,  help_text="How many seconds does the change of weapon take to shoot again")
    spawn_lock_time                 = models.SmallIntegerField(default=10, help_text="How many seconds is a spawn locked after having been used or having been next to player")          
    revive_waiting_time             = models.SmallIntegerField(default=10, help_text="How many seconds has a player to wait to respawn")          
    player_delay_tolerance          = models.SmallIntegerField(default=3,  help_text="How many seconds is it tolerated to be disconnected and not leave the game")
    player_not_responding_time      = models.SmallIntegerField(default=10, help_text="How many seconds has the player to wait after rejoining when disconnected")
    player_occupied_spawn_time      = models.FloatField       (default=0.1,help_text="How many seconds waits the player to find a spawn again whenn all are occupied")

    # The Default GameSettings
    default_max_players             = models.SmallIntegerField(default=6,  help_text="How many player at maximum")
    default_gamemode                = models.SmallIntegerField(default=0,  help_text="default gamemode")
    default_winscore                = models.SmallIntegerField(default=20, help_text="How many kills till game ends")  
    default_max_endtime             = models.SmallIntegerField(default=30, help_text="How many minutes till the game ends")


    #Bullets
    start_position_bullet           = models.FloatField       (default=.5, help_text="How many blocks from the player should a bullet start")
    accuracy_reduction              = models.FloatField       (default=.11,help_text="The radians plus minus range for random calculation")
    hit_box                         = models.FloatField       (default=.4, help_text="How many blocks away from the realy players location")

    wall_hit_box                    = models.FloatField       (default=.4, help_text="How many blocks away from the realy players location")
    wall_hit_box_player_tolerance   = models.FloatField       (default=.25,help_text="How many blocks away from wall_hit_box")
    wall_hit_box_bullet_tolerance   = models.FloatField       (default=.15,help_text="How many blocks away from wall_hit_box")