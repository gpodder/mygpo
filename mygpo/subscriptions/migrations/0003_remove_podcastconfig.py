# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_unique_constraint'),
        # ensure that data migration has been executed before model is deleted
        ('usersettings', '0002_move_existing'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='podcastconfig',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='podcastconfig',
            name='podcast',
        ),
        migrations.RemoveField(
            model_name='podcastconfig',
            name='user',
        ),
        migrations.DeleteModel(
            name='PodcastConfig',
        ),
    ]
