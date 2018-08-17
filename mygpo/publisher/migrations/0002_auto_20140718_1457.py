# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('publisher', '0001_initial')]

    operations = [
        migrations.AlterUniqueTogether(
            name='publishedpodcast', unique_together=set([('publisher', 'podcast')])
        )
    ]
