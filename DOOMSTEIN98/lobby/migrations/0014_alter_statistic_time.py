# Generated by Django 4.0.4 on 2022-05-02 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lobby', '0013_alter_statistic_duration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statistic',
            name='time',
            field=models.DateTimeField(auto_now_add=True, unique=True),
        ),
    ]
