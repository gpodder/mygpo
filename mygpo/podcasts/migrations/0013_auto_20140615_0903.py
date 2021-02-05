# encoding: utf8


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("podcasts", "0012_podcast_update_interval")]

    operations = [
        migrations.AlterField(
            model_name="episode",
            name="mimetypes",
            field=models.CharField(max_length=100),
        )
    ]
