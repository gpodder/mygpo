# encoding: utf8


from django.db import models, migrations
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [("podcasts", "0013_auto_20140615_0903")]

    operations = [
        migrations.AlterField(
            model_name="episode",
            name="created",
            field=models.DateTimeField(default=timezone.now),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="created",
            field=models.DateTimeField(default=timezone.now),
        ),
    ]
