# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcastlists', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='podcastlist',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='podcastlist',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
