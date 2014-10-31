# encoding: utf8


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0005_auto_20140610_1854'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='outdated',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AlterField(
            model_name='podcast',
            name='outdated',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='guid',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
