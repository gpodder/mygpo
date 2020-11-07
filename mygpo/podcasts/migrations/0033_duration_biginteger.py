# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("podcasts", "0032_episode_order_bigint")]

    operations = [
        migrations.AlterField(
            model_name="episode",
            name="duration",
            field=models.BigIntegerField(null=True),
            preserve_default=True,
        )
    ]
