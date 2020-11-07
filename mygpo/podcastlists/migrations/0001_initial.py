# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PodcastList",
            fields=[
                (
                    "id",
                    models.UUIDField(max_length=32, serialize=False, primary_key=True),
                ),
                ("title", models.CharField(max_length=512)),
                ("slug", models.SlugField(max_length=128)),
                ("created", models.DateTimeField()),
                ("modified", models.DateTimeField()),
                (
                    "user",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="PodcastListEntry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("modified", models.DateTimeField(auto_now=True)),
                ("order", models.PositiveSmallIntegerField()),
                ("object_id", models.UUIDField(max_length=32)),
                (
                    "content_type",
                    models.ForeignKey(
                        to="contenttypes.ContentType",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "podcastlist",
                    models.ForeignKey(
                        related_name="entries",
                        to="podcastlists.PodcastList",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name="podcastlistentry",
            unique_together=set(
                [("podcastlist", "order"), ("podcastlist", "content_type", "object_id")]
            ),
        ),
        migrations.AlterUniqueTogether(
            name="podcastlist", unique_together=set([("user", "slug")])
        ),
    ]
