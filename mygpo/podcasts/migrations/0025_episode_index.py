# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('podcasts', '0024_episodes_index')]

    operations = [
        migrations.AlterIndexTogether(
            name='episode', index_together=set([('podcast', 'outdated', 'released')])
        )
    ]
