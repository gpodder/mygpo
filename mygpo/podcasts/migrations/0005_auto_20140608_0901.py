# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0004_podcast_restrictions'),
    ]

    operations = [
        migrations.AddField(
            model_name='podcast',
            name='twitter',
            field=models.CharField(max_length=15, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='podcast',
            name='restrictions',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
    ]
