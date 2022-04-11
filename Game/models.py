from django.db import models

# Create your models here.
class GameList(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class Players(models.Model):
    player = models.ForeignKey(GameList, on_delete=models.CASCADE)