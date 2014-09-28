# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    replaces = [(b'categories', '0001_initial'), (b'categories', '0002_auto_20140927_1501'), (b'categories', '0003_category_num_entries'), (b'categories', '0004_auto_20140927_1540')]

    dependencies = [
        ('podcasts', '0029_episode_index_toplist'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=1000)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CategoryEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('category', models.ForeignKey(to='categories.Category')),
                ('podcast', models.ForeignKey(to='podcasts.Podcast')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CategoryTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tag', models.SlugField(unique=True)),
                ('category', models.ForeignKey(related_name=b'tags', to='categories.Category')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='categoryentry',
            unique_together=set([('category', 'podcast')]),
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name': 'Category', 'verbose_name_plural': 'Categories'},
        ),
        migrations.AddField(
            model_name='category',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2014, 9, 28, 13, 26, 28, 914038), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2014, 9, 28, 13, 26, 28, 914095), auto_now=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='categoryentry',
            name='category',
            field=models.ForeignKey(related_name=b'entries', to='categories.Category'),
        ),
        migrations.AlterField(
            model_name='categoryentry',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterIndexTogether(
            name='category',
            index_together=set([('modified',)]),
        ),
        migrations.AlterIndexTogether(
            name='categoryentry',
            index_together=set([('category', 'modified')]),
        ),
        migrations.AddField(
            model_name='category',
            name='num_entries',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterIndexTogether(
            name='category',
            index_together=set([('modified', 'num_entries')]),
        ),
    ]
