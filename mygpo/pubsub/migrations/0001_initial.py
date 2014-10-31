# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0028_episode_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='HubSubscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('topic_url', models.CharField(unique=True, max_length=2048)),
                ('hub_url', models.CharField(max_length=1000)),
                ('verify_token', models.CharField(max_length=32)),
                ('mode', models.CharField(blank=True, max_length=11, choices=[('subscribe', 'subscribe'), ('unsubscribe', 'unsubscribe')])),
                ('verified', models.BooleanField(default=False)),
                ('podcast', models.ForeignKey(to='podcasts.Podcast', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
