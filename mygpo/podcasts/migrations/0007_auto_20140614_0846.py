# encoding: utf8


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("podcasts", "0006_auto_20140614_0836")]

    operations = [
        migrations.AlterField(
            model_name="episode",
            name="guid",
            field=models.CharField(max_length=200, null=True),
        )
    ]
