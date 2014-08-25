# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0026_slug_index'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='episode',
            index_together=set([('podcast', 'released'), ('podcast', 'outdated', 'released')]),
        ),
    ]
