# Generated by Django 4.0.4 on 2022-05-01 14:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lobby', '0007_rename_settings_setting'),
    ]

    operations = [
        migrations.RenameField(
            model_name='setting',
            old_name='default_max_endscore',
            new_name='default_max_endtime',
        ),
    ]