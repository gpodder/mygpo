# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0014_auto_20140615_1032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slug',
            name='scope',
            field=models.CharField(db_index=True, max_length=32, blank=True),
        ),
        migrations.AlterField(
            model_name='url',
            name='scope',
            field=models.CharField(db_index=True, max_length=32, blank=True),
        ),
    ]
