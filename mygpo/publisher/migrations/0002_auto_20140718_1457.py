# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('publisher', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='publishedpodcast',
            unique_together=set([(b'publisher', b'podcast')]),
        ),
    ]
