from django.db import models

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
    name = models.CharField(max_length=50, unique=True)
    ammunition = models.IntegerField(default=30)
    latency = models.DecimalField(max_digits=10, decimal_places=2, default=0.1)
    damage = models.DecimalField(max_digits=10, decimal_places=2, default=20)
    skin = models.IntegerField(default=1)

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
    name = models.CharField(max_length=50, unique=True)
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    mode = models.IntegerField(default=0)
    max_players = models.SmallIntegerField(default=4)
    current_players = models.SmallIntegerField(default=0)
    game_runtime = models.IntegerField(default=10)
    start_weapon = models.ForeignKey(Weapon, on_delete=models.CASCADE)

    def __str__(self) -> str:
        """ Prints user data

        Returns:
            str: Lobby name
        """
        return self.name