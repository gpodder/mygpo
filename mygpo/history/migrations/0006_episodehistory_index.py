# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("history", "0005_episodehistoryentry")]

    operations = [
        migrations.AlterIndexTogether(
            name="episodehistoryentry",
            index_together=set(
                [
                    ("user", "action", "episode"),
                    ("user", "client", "episode", "action", "timestamp"),
                ]
            ),
        )
    ]
