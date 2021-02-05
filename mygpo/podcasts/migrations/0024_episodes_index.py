# -*- coding: utf-8 -*-


from django.db import migrations


def forward(apps, schema_editor):

    # This index can apparently not be created on sqlite
    # As it is not recommended for production use, we can just
    # skip the index there
    if schema_editor.connection.vendor == "sqlite":
        return

    migrations.RunSQL(
        sql=[
            (
                "CREATE INDEX episodes_podcast_hasreleased "
                "ON podcasts_episode "
                "(podcast_id, (released IS NOT NULL) DESC, released DESC);",
                None,
            )
        ]
    )


def reverse(apps, schema_editor):
    migrations.RunSQL([("DROP INDEX IF EXISTS episodes_podcast_hasreleased;", None)])


class Migration(migrations.Migration):

    dependencies = [("podcasts", "0023_auto_20140729_1711")]

    operations = [
        # Wrap RunSQL in RunPython to check for DB backend
        # http://stackoverflow.com/a/37521148/693140
        migrations.RunPython(code=forward, reverse_code=reverse)
    ]
