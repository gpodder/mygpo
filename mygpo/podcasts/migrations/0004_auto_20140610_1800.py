# encoding: utf8


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("podcasts", "0003_auto_20140610_1752")]

    operations = [
        migrations.AlterField(
            model_name="podcast",
            name="author",
            field=models.CharField(max_length=150, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="episode",
            name="author",
            field=models.CharField(max_length=150, null=True, blank=True),
        ),
    ]
