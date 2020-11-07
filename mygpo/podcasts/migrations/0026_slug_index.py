# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("podcasts", "0025_episode_index")]

    operations = [
        migrations.AlterIndexTogether(
            name="slug", index_together=set([("slug", "content_type")])
        )
    ]
