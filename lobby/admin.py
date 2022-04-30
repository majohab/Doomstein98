from django.contrib import admin
from .models import Lobby, Map, Weapon
from django.contrib.auth.models import Group

# config
admin.site.site_header = 'DOOMSTEIN98'

# Register your models here.
admin.site.register(Lobby)
admin.site.register(Map)
admin.site.register(Weapon)
admin.site.unregister(Group)

class LobbyAdminConfig(admin.ModelAdmin):
    """Configuration for lobby table

    Args:
        UserAdmin (Class): Admin config
    """
    search_fields = ('name', 'current_players')
    list_filter = ('map', 'max_players', 
                   'current_players', 'game_runtime')
    ordering = ('name', 'current_players')
    list_display = ('name', 'map', 
                    'max_players', 'game_runtime')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'map', 'max_players', 'current_players', 'game_runtime')
        }),
    )

admin.site.unregister(Lobby)
admin.site.register(Lobby, LobbyAdminConfig)

class MapAdminConfig(admin.ModelAdmin):
    """Configuration for map table

    Args:
        UserAdmin (Class): Admin config
    """
    search_fields = ('name', 'description')
    list_filter = ('name', 'string')
    ordering = ('name', 'string')
    list_display = ('name', 'description')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'string', 'description')
        }),
    )

admin.site.unregister(Map)
admin.site.register(Map, MapAdminConfig)

class WeaponAdminConfig(admin.ModelAdmin):
    """Configuration for map table

    Args:
        UserAdmin (Class): Admin config
    """
    search_fields = ('name', 'ammunition', 
                     'latency', 'damage', 
                     'skin')
    list_filter = ('ammunition', 'latency', 
                   'damage')
    ordering = ('name', 'damage')
    list_display = ('name', 'ammunition', 'damage', 'skin')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'ammunition', 'latency''damage', 'skin')
        }),
    )

admin.site.unregister(Weapon)
admin.site.register(Weapon, WeaponAdminConfig)