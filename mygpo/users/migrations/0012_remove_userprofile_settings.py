# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0011_syncgroup_blank"),
        ("usersettings", "0002_move_existing"),
    ]

    operations = [migrations.RemoveField(model_name="userprofile", name="settings")]
