# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0008_auto_20140614_1152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='podcast',
            name='author',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='author',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
