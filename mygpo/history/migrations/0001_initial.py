# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_syncgroup_protect'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('podcasts', '0023_auto_20140729_1711'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoryEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField()),
                ('action', models.CharField(max_length=11, choices=[('subscribe', 'subscribed'), ('unsubscribe', 'unsubscribed')])),
                ('client', models.ForeignKey(
                    to='users.Client',
                    on_delete=models.CASCADE,
                )),
                ('podcast', models.ForeignKey(
                    to='podcasts.Podcast',
                    on_delete=models.CASCADE,
                )),
                ('user', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    on_delete=models.CASCADE,
                )),
            ],
            options={
                'ordering': ['timestamp'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='historyentry',
            index_together=set([('user', 'podcast'), ('user', 'client')]),
        ),
    ]
