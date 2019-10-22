# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('history', '0008_episodehistory_index')]

    operations = [
        migrations.AlterField(
            model_name='episodehistoryentry',
            name='client',
            field=models.ForeignKey(
                blank=True, to='users.Client', null=True, on_delete=models.CASCADE
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='episodehistoryentry',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='episodehistoryentry',
            name='episode_ref_url',
            field=models.URLField(max_length=2048, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='episodehistoryentry',
            name='podcast_ref_url',
            field=models.URLField(max_length=2048, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='episodehistoryentry',
            name='started',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='episodehistoryentry',
            name='stopped',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='episodehistoryentry',
            name='total',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
