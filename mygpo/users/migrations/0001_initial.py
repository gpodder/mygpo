# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import uuidfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('twitter', models.CharField(max_length=15, null=True)),
                ('suggestions_up_to_date', models.BooleanField(default=False)),
                ('about', models.TextField(blank=True)),
                ('google_email', models.CharField(max_length=100, null=True)),
                ('subscriptions_token', models.CharField(max_length=32, null=True)),
                ('favorite_feeds_token', models.CharField(max_length=32, null=True)),
                ('publisher_update_token', models.CharField(max_length=32, null=True)),
                ('userpage_token', models.CharField(max_length=32, null=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
                ('uuid', uuidfield.fields.UUIDField(unique=True, max_length=32)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
