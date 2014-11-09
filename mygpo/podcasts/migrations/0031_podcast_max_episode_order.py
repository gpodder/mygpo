# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0030_ordered_episode'),
    ]

    operations = [
        migrations.AddField(
            model_name='podcast',
            name='max_episode_order',
            field=models.PositiveIntegerField(default=None, null=True),
            preserve_default=True,
        ),
    ]
