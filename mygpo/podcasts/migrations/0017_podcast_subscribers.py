# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0015_auto_20140616_1105'),
    ]

    operations = [
        migrations.AddField(
            model_name='podcast',
            name='subscribers',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
    ]
