# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chapters', '0001_initial'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='chapter',
            index_together=set([('user', 'episode', 'created'), ('episode', 'user', 'start', 'end')]),
        ),
    ]
