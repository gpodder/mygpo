# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0023_auto_20140729_1711'),
    ]

    operations = [
        migrations.RunSQL(
            sql = 'CREATE INDEX episodes_podcast_hasreleased ON podcasts_episode (podcast_id, (released IS NOT NULL) DESC, released DESC);',
            reverse_sql = 'DROP INDEX IF EXISTS episodes_podcast_hasreleased;',
        )
    ]
