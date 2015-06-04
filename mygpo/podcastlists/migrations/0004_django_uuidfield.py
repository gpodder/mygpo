# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcastlists', '0003_entries_ordering'),
    ]

    operations = [
        migrations.AlterField(
            model_name='podcastlist',
            name='id',
            field=models.UUIDField(serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='podcastlistentry',
            name='object_id',
            field=models.UUIDField(),
        ),
    ]
