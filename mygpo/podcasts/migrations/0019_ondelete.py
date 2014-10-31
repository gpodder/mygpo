# encoding: utf8


from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0018_podcast_released'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slug',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=django.db.models.deletion.PROTECT, to_field='id'),
        ),
        migrations.AlterField(
            model_name='podcast',
            name='group',
            field=models.ForeignKey(to='podcasts.PodcastGroup', on_delete=django.db.models.deletion.PROTECT, to_field=b'id', null=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=django.db.models.deletion.PROTECT, to_field='id'),
        ),
        migrations.AlterField(
            model_name='mergeduuid',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=django.db.models.deletion.PROTECT, to_field='id'),
        ),
        migrations.AlterField(
            model_name='url',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', on_delete=django.db.models.deletion.PROTECT, to_field='id'),
        ),
        migrations.AlterField(
            model_name='episode',
            name='podcast',
            field=models.ForeignKey(to='podcasts.Podcast', on_delete=django.db.models.deletion.PROTECT, to_field=b'id'),
        ),
    ]
