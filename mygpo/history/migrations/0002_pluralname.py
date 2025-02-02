# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("history", "0001_initial")]

    operations = [
        migrations.AlterModelOptions(
            name="historyentry",
            options={
                "ordering": ["timestamp"],
                "verbose_name_plural": "History Entries",
            },
        )
    ]
