# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('users', '0002_auto_20140718_1457')]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='user_agent',
            field=models.CharField(max_length=300, null=True, blank=True),
        )
    ]
