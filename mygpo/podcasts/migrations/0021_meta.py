# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0020_extend_episode_mimetypes'),
        ('contenttypes', '__first__'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='episode',
            options={'ordering': ['-released']},
        ),
        migrations.AlterModelOptions(
            name='mergeduuid',
            options={'verbose_name': 'Merged UUID', 'verbose_name_plural': 'Merged UUIDs'},
        ),
        migrations.AlterModelOptions(
            name='slug',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='url',
            options={'ordering': ['order'], 'verbose_name': 'URL', 'verbose_name_plural': 'URLs'},
        ),
    ]
