# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcastlists', '0002_updateinfomodel'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='podcastlistentry',
            options={'ordering': ['order']},
        ),
    ]
