# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0002_auto_20140607_1424'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='filesize',
            field=models.BigIntegerField(null=True),
        ),
    ]
