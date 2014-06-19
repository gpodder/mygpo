# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0017_podcast_subscribers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='released',
            field=models.DateTimeField(null=True, db_index=True),
        ),
    ]
