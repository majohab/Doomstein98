# Generated by Django 4.0.4 on 2022-05-01 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lobby', '0004_remove_weapon_skin'),
    ]

    operations = [
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tick_rate', models.FloatField(default=0.016666666666666666)),
                ('player_speed', models.FloatField(default=0.1, help_text='Get calculated as divisor')),
                ('rotation_speed', models.FloatField(default=1, help_text='Get calculated as divisor')),
                ('bullet_speed', models.FloatField(default=0.016666666666666666, help_text='Get calculated as divisor')),
                ('min_munition', models.FloatField(default=0.2, help_text='The minimum percentage of ammunition calculating randomly in a munition package of a weapon')),
                ('max_munition', models.FloatField(default=1, help_text='The maximum percentage of ammunition calculating randomly in a munition package of a weapon')),
                ('step_munition', models.FloatField(default=0.2, help_text='The steps between min and max ammunition calculating randomly in a munition package of a weapon')),
                ('default_ammunition_delay', models.FloatField(default=2, help_text='The delay in minutes till the ammunition is respawned')),
                ('spawn_index', models.SmallIntegerField(default=50, help_text='The starting index for handling spawns. It should be at least as high')),
                ('shot_animation_modulo', models.SmallIntegerField(default=100, help_text='How many Frames are needed to display an animation for shooting')),
                ('move_animation_bullet_modulo', models.SmallIntegerField(default=100, help_text='How many Frames are needed to display an animation for moving a player')),
                ('move_animation_player_modulo', models.SmallIntegerField(default=100, help_text='How many Frames are needed to display an animation for moving a bullet')),
                ('hit_animation_duration', models.SmallIntegerField(default=1, help_text='How many seconds are needed to display an animation for dying')),
                ('died_animation_duration', models.SmallIntegerField(default=10, help_text='How many seconds are needed to display an animation for getting hit')),
                ('change_weapon_delay', models.SmallIntegerField(default=1, help_text='How many seconds does the change of weapon take to shoot again')),
                ('spawn_lock_time', models.SmallIntegerField(default=10, help_text='How many seconds is a spawn locked after having been used or having been next to player')),
                ('revive_waiting_time', models.SmallIntegerField(default=10, help_text='How many seconds has a player to wait to respawn')),
                ('player_delay_tolerance', models.SmallIntegerField(default=3, help_text='How many seconds is it tolerated to be disconnected and not leave the game')),
                ('player_not_responding_time', models.SmallIntegerField(default=10, help_text='How many seconds has the player to wait after rejoining when disconnected')),
                ('player_occupied_spawn_time', models.FloatField(default=0.1, help_text='How many seconds waits the player to find a spawn again whenn all are occupied')),
                ('default_max_players', models.SmallIntegerField(default=6, help_text='How many player at maximum')),
                ('default_gamemode', models.SmallIntegerField(default=0, help_text='default gamemode')),
                ('default_winscore', models.SmallIntegerField(default=20, help_text='How many kills till game ends')),
                ('default_max_endscore', models.SmallIntegerField(default=30, help_text='How many minutes till the game ends')),
                ('accuracy_reduction', models.FloatField(default=0.11, help_text='The radians plus minus range for random calculation')),
                ('hit_box', models.FloatField(default=0.4, help_text='How many blocks away from the realy players location')),
                ('wall_hit_box', models.FloatField(default=0.4, help_text='How many blocks away from the realy players location')),
                ('wall_hit_box_player_tolerance', models.FloatField(default=0.25, help_text='How many blocks away from wall_hit_box')),
                ('wall_hit_box_bullet_tolerance', models.FloatField(default=0.15, help_text='How many blocks away from wall_hit_box')),
            ],
        ),
    ]
