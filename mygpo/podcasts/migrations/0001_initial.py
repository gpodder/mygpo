# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import uuidfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='PodcastGroup',
            fields=[
                ('id', uuidfield.fields.UUIDField(max_length=32, serialize=False, primary_key=True)),
                ('title', models.CharField(max_length=1000, blank=True)),
                ('subtitle', models.CharField(max_length=1000, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MergedUUID',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', uuidfield.fields.UUIDField(unique=True, max_length=32)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', to_field='id')),
                ('object_id', uuidfield.fields.UUIDField(max_length=32)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Slug',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField()),
                ('scope', uuidfield.fields.UUIDField(max_length=32, null=True)),
                ('slug', models.SlugField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', to_field='id')),
                ('object_id', uuidfield.fields.UUIDField(max_length=32)),
            ],
            options={
                'unique_together': set([(b'slug', b'scope'), (b'content_type', b'object_id', b'order')]),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tag', models.SlugField()),
                ('source', models.PositiveSmallIntegerField(choices=[(1, b'Feed'), (2, b'delicious'), (4, b'User')])),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', to_field='id')),
                ('object_id', uuidfield.fields.UUIDField(max_length=32)),
            ],
            options={
                'unique_together': set([(b'tag', b'source', b'content_type', b'object_id')]),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='URL',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField()),
                ('scope', uuidfield.fields.UUIDField(max_length=32, null=True)),
                ('url', models.URLField(max_length=1000)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', to_field='id')),
                ('object_id', uuidfield.fields.UUIDField(max_length=32)),
            ],
            options={
                'unique_together': set([(b'url', b'scope'), (b'content_type', b'object_id', b'order')]),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Podcast',
            fields=[
                ('id', uuidfield.fields.UUIDField(max_length=32, serialize=False, primary_key=True)),
                ('title', models.CharField(max_length=1000, blank=True)),
                ('subtitle', models.CharField(max_length=1000, blank=True)),
                ('description', models.TextField(blank=True)),
                ('link', models.URLField(max_length=1000, null=True)),
                ('language', models.CharField(max_length=10, null=True)),
                ('last_update', models.DateTimeField()),
                ('created', models.DateTimeField()),
                ('modified', models.DateTimeField(auto_now=True)),
                ('license', models.CharField(max_length=100, null=True)),
                ('flattr_url', models.URLField(max_length=1000, null=True)),
                ('content_types', models.CharField(max_length=20, blank=True)),
                ('outdated', models.BooleanField(default=False)),
                ('author', models.CharField(max_length=100, null=True, blank=True)),
                ('logo_url', models.URLField(max_length=1000, null=True)),
                ('group', models.ForeignKey(to='podcasts.PodcastGroup', to_field=b'id', null=True)),
                ('group_member_name', models.CharField(max_length=30, null=True)),
                ('common_episode_title', models.CharField(max_length=50, blank=True)),
                ('new_location', models.URLField(max_length=1000, null=True)),
                ('latest_episode_timestamp', models.DateTimeField(null=True)),
                ('episode_count', models.PositiveIntegerField()),
                ('hub', models.URLField(null=True)),
                ('related_podcasts', models.ManyToManyField(to=b'podcasts.Podcast')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('id', uuidfield.fields.UUIDField(max_length=32, serialize=False, primary_key=True)),
                ('title', models.CharField(max_length=1000, blank=True)),
                ('subtitle', models.CharField(max_length=1000, blank=True)),
                ('description', models.TextField(blank=True)),
                ('link', models.URLField(max_length=1000, null=True)),
                ('language', models.CharField(max_length=10, null=True)),
                ('last_update', models.DateTimeField()),
                ('created', models.DateTimeField()),
                ('modified', models.DateTimeField(auto_now=True)),
                ('license', models.CharField(max_length=100, null=True)),
                ('flattr_url', models.URLField(max_length=1000, null=True)),
                ('content_types', models.CharField(max_length=20, blank=True)),
                ('outdated', models.BooleanField(default=False)),
                ('author', models.CharField(max_length=100, null=True, blank=True)),
                ('guid', models.CharField(max_length=50, null=True)),
                ('content', models.TextField()),
                ('released', models.DateTimeField(null=True)),
                ('duration', models.PositiveIntegerField(null=True)),
                ('filesize', models.PositiveIntegerField(null=True)),
                ('mimetypes', models.CharField(max_length=50)),
                ('listeners', models.PositiveIntegerField(null=True)),
                ('podcast', models.ForeignKey(to='podcasts.Podcast', to_field=b'id')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
