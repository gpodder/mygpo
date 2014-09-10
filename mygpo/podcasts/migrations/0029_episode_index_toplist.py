# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0028_episode_indexes'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='episode',
            index_together=set([('language', 'listeners'), ('released', 'podcast'), ('podcast', 'released'), ('podcast', 'outdated', 'released')]),
        ),
    ]
