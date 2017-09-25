# encoding: utf8


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='podcast',
            name='twitter',
            field=models.CharField(max_length=15, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='podcast',
            name='restrictions',
            field=models.CharField(max_length=20, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='podcast',
            name='episode_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='episode',
            name='last_update',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='podcastgroup',
            name='title',
            field=models.CharField(db_index=True, max_length=1000, blank=True),
        ),
        migrations.AlterField(
            model_name='podcast',
            name='last_update',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='slug',
            name='slug',
            field=models.SlugField(max_length=150),
        ),
        migrations.AlterField(
            model_name='episode',
            name='title',
            field=models.CharField(db_index=True, max_length=1000, blank=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='filesize',
            field=models.BigIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='podcast',
            name='title',
            field=models.CharField(db_index=True, max_length=1000, blank=True),
        ),
        migrations.AlterField(
            model_name='url',
            name='url',
            field=models.URLField(max_length=2048),
        ),
    ]
