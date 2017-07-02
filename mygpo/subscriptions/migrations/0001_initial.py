# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_syncgroup_protect'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('podcasts', '0023_auto_20140729_1711'),
    ]

    operations = [
        migrations.CreateModel(
            name='PodcastConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('settings', models.TextField(default='{}')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('podcast', models.ForeignKey(to='podcasts.Podcast', on_delete=django.db.models.deletion.PROTECT)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('deleted', models.BooleanField(default=False)),
                ('ref_url', models.URLField(max_length=2048)),
                ('created', models.DateTimeField()),
                ('modified', models.DateTimeField()),
                ('client', models.ForeignKey(to='users.Client')),
                ('podcast', models.ForeignKey(to='podcasts.Podcast', on_delete=django.db.models.deletion.PROTECT)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='subscription',
            unique_together=set([('user', 'client', 'podcast')]),
        ),
        migrations.AlterIndexTogether(
            name='subscription',
            index_together=set([('user', 'client')]),
        ),
    ]
