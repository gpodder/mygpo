# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("podcasts", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="PublishedPodcast",
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
                (
                    "podcast",
                    models.ForeignKey(to="podcasts.Podcast", on_delete=models.CASCADE),
                ),
                (
                    "publisher",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        )
    ]
