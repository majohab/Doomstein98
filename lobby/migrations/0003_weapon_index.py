# Generated by Django 4.0.4 on 2022-05-01 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lobby', '0002_map_len'),
    ]

    operations = [
        migrations.AddField(
            model_name='weapon',
            name='index',
            field=models.PositiveSmallIntegerField(default=0, unique=True),
        ),
    ]