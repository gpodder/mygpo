# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0007_episodehistory_index'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='episodehistoryentry',
            index_together=set([('user', 'action', 'episode'), ('user', 'client', 'episode', 'action', 'timestamp'), ('episode', 'timestamp'), ('user', 'episode', 'timestamp')]),
        ),
    ]
