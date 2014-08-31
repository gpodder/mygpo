# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('pubsub', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hubsubscription',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2014, 8, 31, 12, 59, 26, 484445), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='hubsubscription',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2014, 8, 31, 12, 59, 36, 369407), auto_now=True),
            preserve_default=False,
        ),
    ]
