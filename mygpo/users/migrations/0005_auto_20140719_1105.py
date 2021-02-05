# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("users", "0004_auto_20140718_1655")]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="activation_key",
            field=models.CharField(max_length=40, null=True),
        )
    ]
