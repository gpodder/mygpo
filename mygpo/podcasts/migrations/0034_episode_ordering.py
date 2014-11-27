# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0033_duration_biginteger'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='episode',
            options={'ordering': ['-order', '-released']},
        ),
        migrations.AlterIndexTogether(
            name='episode',
            index_together=set([('podcast', 'order', 'released'),
                                ('released', 'podcast'),
                                ('podcast', 'released'),
                                ('language', 'listeners'),
                                ('podcast', 'outdated', 'released')]),
        ),
    ]
