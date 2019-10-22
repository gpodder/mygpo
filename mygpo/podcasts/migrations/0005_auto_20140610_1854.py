# encoding: utf8


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('podcasts', '0004_auto_20140610_1800')]

    operations = [
        migrations.AlterField(
            model_name='slug',
            name='scope',
            field=models.UUIDField(max_length=32, null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='url',
            name='scope',
            field=models.UUIDField(max_length=32, null=True, db_index=True),
        ),
    ]
