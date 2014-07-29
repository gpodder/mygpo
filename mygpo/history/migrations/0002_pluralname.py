# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historyentry',
            options={'ordering': [b'timestamp'], 'verbose_name_plural': b'History Entries'},
        ),
    ]
