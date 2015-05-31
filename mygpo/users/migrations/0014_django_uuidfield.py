# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_remove_userprofile_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='id',
            field=models.UUIDField(serialize=False, primary_key=True),
        ),
    ]
