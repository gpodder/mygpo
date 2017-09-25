# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('podcasts', '0023_auto_20140729_1711'),
    ]

    operations = [
        migrations.CreateModel(
            name='FavoriteEpisode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('episode', models.ForeignKey(to='podcasts.Episode', on_delete=django.db.models.deletion.PROTECT)),
                ('user', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    on_delete=models.CASCADE,
                )),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
