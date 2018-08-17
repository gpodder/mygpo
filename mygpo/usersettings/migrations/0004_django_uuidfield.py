# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('usersettings', '0003_meta_verbose_name')]

    operations = [
        migrations.AlterField(
            model_name='usersettings',
            name='object_id',
            field=models.UUIDField(null=True, blank=True),
        )
    ]
