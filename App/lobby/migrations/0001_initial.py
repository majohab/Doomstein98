# Generated by Django 4.0.4 on 2022-05-01 11:47

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Map',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('string', models.CharField(max_length=10000, unique=True)),
                ('description', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Weapon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('ammunition', models.PositiveSmallIntegerField(default=30, validators=[django.core.validators.MinValueValidator(1, 'The Weapon has to have at least 1 bullet')])),
                ('latency', models.FloatField(default=0.1, validators=[django.core.validators.MinValueValidator(0.01), django.core.validators.MaxValueValidator(10)])),
                ('damage', models.PositiveSmallIntegerField(default=20, validators=[django.core.validators.MinValueValidator(1, 'The Weapon has to do at least one damage')])),
                ('skin', models.PositiveSmallIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Lobby',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('mode', models.PositiveSmallIntegerField(default=0)),
                ('max_players', models.PositiveSmallIntegerField(default=4, validators=[django.core.validators.MinValueValidator(2, 'To play reasonably, you should play at least with two player'), django.core.validators.MaxValueValidator(10, 'The Server can not handle more players')])),
                ('current_players', models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(models.PositiveSmallIntegerField(default=4, validators=[django.core.validators.MinValueValidator(2, 'To play reasonably, you should play at least with two player'), django.core.validators.MaxValueValidator(10, 'The Server can not handle more players')]))])),
                ('game_runtime', models.PositiveSmallIntegerField(default=10, validators=[django.core.validators.MinValueValidator(2), django.core.validators.MaxValueValidator(60)])),
                ('map', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lobby.map')),
            ],
        ),
    ]
