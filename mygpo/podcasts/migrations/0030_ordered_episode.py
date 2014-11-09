# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0029_episode_index_toplist'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='episode',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='episode',
            name='order',
            field=models.PositiveIntegerField(default=None, null=True),
            preserve_default=True,
        ),
    ]
