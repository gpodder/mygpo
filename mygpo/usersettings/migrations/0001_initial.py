# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserSettings",
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
                ("settings", models.TextField(default="{}")),
                ("object_id", models.UUIDField(max_length=32, null=True, blank=True)),
                (
                    "content_type",
                    models.ForeignKey(
                        blank=True,
                        to="contenttypes.ContentType",
                        null=True,
                        on_delete=models.PROTECT,
                    ),
                ),
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
        migrations.AlterUniqueTogether(
            name="usersettings",
            unique_together=set([("user", "content_type", "object_id")]),
        ),
        # PostgreSQL does not consider null values for unique constraints;
        # UserSettings for Users have no content_object; the following ensures
        # there can only be one such entry per user
        migrations.RunSQL(
            [
                (
                    "CREATE UNIQUE INDEX usersettings_unique_null "
                    "ON usersettings_usersettings (user_id) "
                    "WHERE content_type_id IS NULL;",
                    None,
                )
            ],
            [("DROP INDEX IF EXISTS usersettings_unique_null;", None)],
        ),
    ]
