# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0021_meta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='listeners',
            field=models.PositiveIntegerField(null=True, db_index=True),
        ),
    ]
