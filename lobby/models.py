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
    topology = models.CharField(max_length=500, unique=True)
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
    name        = models.CharField                      (max_length=50, unique=True)
    ammunition  = models.PositiveSmallIntegerField      (default=30,  validators=[validator.MinValueValidator(1, 'The Weapon has to have at least 1 bullet')])
    latency     = models.FloatField                     (default=0.1, validators=[validator.MinValueValidator(0.01),validator.MaxValueValidator(10)]) # in sec
    damage      = models.PositiveSmallIntegerField      (default=20,  validators=[validator.MinValueValidator(1, "The Weapon has to do at least one damage")])
    skin        = models.PositiveSmallIntegerField      (default=1)

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
    name            = models.CharField                  (max_length=50, unique=True)
    map             = models.ForeignKey                 (Map, on_delete=models.CASCADE)
    mode            = models.PositiveSmallIntegerField  (default=0)
    max_players     = models.PositiveSmallIntegerField  (default=4, validators=[validator.MinValueValidator(2,"To play reasonably, you should play at least with two player"), validator.MaxValueValidator(MAX_PLAYERS, "The Server can not handle more players")])
    current_players = models.PositiveSmallIntegerField  (default=0, validators=[validator.MaxValueValidator(max_players)])
    game_runtime    = models.PositiveSmallIntegerField  (default=10,validators=[validator.MinValueValidator(2), validator.MaxValueValidator(60)])
    start_weapon    = models.ForeignKey                 (Weapon, on_delete=models.CASCADE) # Bit field - What weapons was chosen


    def __str__(self) -> str:
        """ Prints user data

        Returns:
            str: Lobby name
        """
        return self.name