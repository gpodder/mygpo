# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [('users', '0006_auto_20140726_0928')]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='sync_group',
            field=models.ForeignKey(
                to='users.SyncGroup',
                on_delete=django.db.models.deletion.PROTECT,
                null=True,
            ),
        )
    ]
