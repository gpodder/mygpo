# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_syncgroup_protect'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql = 'CREATE INDEX django_auth_user_email ON auth_user (email, username);',
            reverse_sql = 'DROP INDEX IF EXISTS django_auth_user_email;',
        )
    ]
