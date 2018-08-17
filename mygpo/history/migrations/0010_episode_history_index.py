# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('history', '0009_blank_fields')]

    operations = [
        migrations.AlterIndexTogether(
            name='episodehistoryentry',
            index_together=set(
                [
                    ('user', 'action', 'episode'),
                    ('user', 'timestamp'),
                    ('user', 'client', 'episode', 'action', 'timestamp'),
                    ('episode', 'timestamp'),
                    ('user', 'episode', 'timestamp'),
                ]
            ),
        )
    ]
