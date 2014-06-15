# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0013_auto_20140615_0903'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='created',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
        migrations.AlterField(
            model_name='podcast',
            name='created',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
    ]
