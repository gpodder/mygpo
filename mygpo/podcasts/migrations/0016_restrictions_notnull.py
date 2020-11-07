# encoding: utf8


from django.db import models, migrations


def set_restriction(apps, schema_editor):
    Podcast = apps.get_model("podcasts", "Podcast")
    for podcast in Podcast.objects.filter(restrictions__isnull=True):
        podcast.restrictions = ""
        podcast.save()


class Migration(migrations.Migration):

    dependencies = [("podcasts", "0015_auto_20140616_2126")]

    operations = [
        migrations.RunPython(set_restriction),
        migrations.AlterField(
            model_name="podcast",
            name="restrictions",
            field=models.CharField(default="", max_length=20, blank=True),
        ),
    ]
