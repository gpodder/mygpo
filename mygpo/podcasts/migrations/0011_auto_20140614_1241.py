# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0010_auto_20140614_1232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='podcast',
            name='common_episode_title',
            field=models.CharField(max_length=100, blank=True),
        ),
    ]
