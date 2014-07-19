# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0003_auto_20140718_1502'),
    ]

    operations = [
        migrations.CreateModel(
            name='SyncGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='client',
            name='sync_group',
            field=models.ForeignKey(to='users.SyncGroup', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='activation_key',
            field=models.CharField(max_length=32, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='settings',
            field=models.TextField(default=b'{}'),
            preserve_default=True,
        ),
    ]
