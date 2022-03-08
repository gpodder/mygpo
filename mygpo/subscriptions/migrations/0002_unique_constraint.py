# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("subscriptions", "0001_initial")]

    operations = [
        migrations.AlterUniqueTogether(
            name="podcastconfig", unique_together=set([("user", "podcast")])
        )
    ]
