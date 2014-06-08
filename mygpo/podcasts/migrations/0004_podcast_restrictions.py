# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0003_auto_20140607_1458'),
    ]

    operations = [
        migrations.AddField(
            model_name='podcast',
            name='restrictions',
            field=models.CharField(default=b'', max_length=20, blank=True),
            preserve_default=True,
        ),
    ]
