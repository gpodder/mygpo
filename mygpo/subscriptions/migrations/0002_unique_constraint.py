# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='podcastconfig',
            unique_together=set([(b'user', b'podcast')]),
        ),
    ]
