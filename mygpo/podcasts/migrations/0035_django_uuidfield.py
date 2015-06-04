# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0034_episode_ordering'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='id',
            field=models.UUIDField(serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='mergeduuid',
            name='object_id',
            field=models.UUIDField(),
        ),
        migrations.AlterField(
            model_name='mergeduuid',
            name='uuid',
            field=models.UUIDField(unique=True),
        ),
        migrations.AlterField(
            model_name='podcast',
            name='id',
            field=models.UUIDField(serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='podcastgroup',
            name='id',
            field=models.UUIDField(serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='slug',
            name='object_id',
            field=models.UUIDField(),
        ),
        migrations.AlterField(
            model_name='tag',
            name='object_id',
            field=models.UUIDField(),
        ),
        migrations.AlterField(
            model_name='url',
            name='object_id',
            field=models.UUIDField(),
        ),
    ]
