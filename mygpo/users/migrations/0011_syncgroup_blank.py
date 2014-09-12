# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_user_profile_related'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='sync_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='users.SyncGroup', null=True),
        ),
    ]
