# -*- coding: utf-8 -*-
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("users", "0012_remove_userprofile_settings")]

    operations = [migrations.RemoveField(model_name="userprofile", name="uuid")]
