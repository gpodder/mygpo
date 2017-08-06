# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0029_episode_index_toplist'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EpisodeState',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(max_length=8, choices=[('download', 'downloaded'), ('play', 'played'), ('delete', 'deleted'), ('new', 'marked as new'), ('flattr', "flattr'd")])),
                ('timestamp', models.DateTimeField()),
                ('episode', models.ForeignKey(
                    to='podcasts.Episode',
                    on_delete=models.CASCADE,
                )),
                ('user', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    on_delete=models.CASCADE,
                )),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='episodestate',
            unique_together=set([('user', 'episode')]),
        ),
    ]
