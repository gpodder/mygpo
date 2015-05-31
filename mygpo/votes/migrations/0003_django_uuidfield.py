# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('votes', '0002_updateinfomodel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vote',
            name='object_id',
            field=models.UUIDField(),
        ),
    ]
