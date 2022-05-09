from django.contrib import admin
from .models import Lobby, Map, Weapon, Setting, Statistic, WeaponStatistic
from django.contrib.auth.models import Group

# config
admin.site.site_header = 'DOOMSTEIN98'

# Register your models here.
admin.site.register(Lobby)
admin.site.register(Map)
admin.site.register(Weapon)
admin.site.register(Setting)
admin.site.register(Statistic)
admin.site.register(WeaponStatistic)
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
    search_fields = ('index','name', 'ammunition', 
                     'latency', 'damage', 
                     )
    list_filter = ('ammunition', 'latency', 
                   'damage')
    ordering = ('name', 'damage')
    list_display = ('index', 'name', 'ammunition', 'damage')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('index', 'name', 'ammunition', 'latency','damage')
        }),
    )

admin.site.unregister(Weapon)
admin.site.register(Weapon, WeaponAdminConfig)

class StatisticAdminConfig(admin.ModelAdmin):
    """Configuration for map table

    Args:
        UserAdmin (Class): Admin config
    """
    ordering = ('username', 'time')  
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username')
        }),
    )

admin.site.unregister(Statistic)
admin.site.register(Statistic, StatisticAdminConfig)

class WeaponStatisticAdminConfig(admin.ModelAdmin):
    """Configuration for map table

    Args:
        UserAdmin (Class): Admin config
    """
    ordering = ('name', 'time')  
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name')
        }),
    )

admin.site.unregister(WeaponStatistic)
admin.site.register(WeaponStatistic, WeaponStatisticAdminConfig)

class SettingAdminConfig(admin.ModelAdmin):
    """Configuration for map table

    Args:
        UserAdmin (Class): Admin config
    """
    ordering = ('index', 'tick_rate')  
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('index')
        }),
    )

admin.site.unregister(Setting)
admin.site.register(Setting, SettingAdminConfig)