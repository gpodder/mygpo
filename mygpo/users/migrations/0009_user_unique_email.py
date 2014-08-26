# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_user_index_email'),
    ]

    operations = [
        migrations.RunSQL(
            sql = 'CREATE UNIQUE INDEX django_auth_unique_email ON auth_user (email);',
            reverse_sql = 'DROP INDEX IF EXISTS django_auth_unique_email;',
        )
    ]
