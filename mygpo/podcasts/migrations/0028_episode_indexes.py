# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('podcasts', '0027_episode_index')]

    operations = [
        migrations.AlterField(
            model_name='podcast',
            name='related_podcasts',
            field=models.ManyToManyField(
                related_name='related_podcasts_rel_+', to='self'
            ),
        ),
        migrations.AlterIndexTogether(
            name='episode',
            index_together=set(
                [
                    ('released', 'podcast'),
                    ('podcast', 'released'),
                    ('podcast', 'outdated', 'released'),
                ]
            ),
        ),
    ]
