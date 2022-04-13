from django.forms import ModelForm
from .models import Lobby, Weapon, Map

# Create your forms here

class LobbyForm(ModelForm):
    """ Form to create lobby

    Inherits:
        ModelForm (Class): Basic model form
    """
    class Meta():
        model = Lobby
        fields = ('name', 'map', 'max_players', 'current_players', 'game_runtime', 'start_weapon')
