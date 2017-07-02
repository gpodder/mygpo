# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('favorites', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='favoriteepisode',
            unique_together=set([('user', 'episode')]),
        ),
    ]
