# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-13 07:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0003_rel_name'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='MergeQueue',
            new_name='MergeTask',
        ),
        migrations.RenameModel(
            old_name='MergeQueueEntry',
            new_name='MergeTaskEntry',
        ),
    ]