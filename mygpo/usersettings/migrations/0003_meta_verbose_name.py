# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usersettings', '0002_move_existing'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='usersettings',
            options={'verbose_name': 'User Settings', 'verbose_name_plural': 'User Settings'},
        ),
    ]
