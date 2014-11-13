# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0031_podcast_max_episode_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='episode',
            options={'ordering': ['-released']},
        ),
        migrations.AlterField(
            model_name='episode',
            name='order',
            field=models.BigIntegerField(default=None, null=True),
            preserve_default=True,
        ),
    ]
