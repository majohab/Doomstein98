# Generated by Django 4.0.4 on 2022-05-02 17:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lobby', '0011_rename_finished_game_statistic_finished_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='statistic',
            old_name='forbbiden',
            new_name='forbidden',
        ),
    ]
