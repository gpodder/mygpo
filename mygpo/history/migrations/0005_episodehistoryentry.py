# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_syncgroup_protect'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('podcasts', '0023_auto_20140729_1711'),
        ('history', '0004_historyentry_episode'),
    ]

    operations = [
        migrations.CreateModel(
            name='EpisodeHistoryEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField()),
                ('created', models.DateTimeField()),
                ('action', models.CharField(max_length=8, choices=[('download', 'downloaded'), ('play', 'played'), ('delete', 'deleted'), ('new', 'marked as new'), ('flattr', "flattr'd")])),
                ('podcast_ref_url', models.URLField(max_length=2048, null=True)),
                ('episode_ref_url', models.URLField(max_length=2048, null=True)),
                ('started', models.IntegerField(null=True)),
                ('stopped', models.IntegerField(null=True)),
                ('total', models.IntegerField(null=True)),
                ('client', models.ForeignKey(to='users.Client', null=True)),
                ('episode', models.ForeignKey(to='podcasts.Episode', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
                'verbose_name_plural': 'Episode History Entries',
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='episodehistoryentry',
            index_together=set([('user', 'client', 'episode', 'action', 'timestamp')]),
        ),
        migrations.RemoveField(
            model_name='historyentry',
            name='episode',
        ),
    ]
