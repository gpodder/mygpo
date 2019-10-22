# encoding: utf8


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('podcasts', '0002_auto_20140609_0916')]

    operations = [
        migrations.AlterField(
            model_name='podcast',
            name='license',
            field=models.CharField(max_length=100, null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='podcast',
            name='flattr_url',
            field=models.URLField(max_length=1000, null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='flattr_url',
            field=models.URLField(max_length=1000, null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='podcast',
            name='language',
            field=models.CharField(max_length=10, null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='language',
            field=models.CharField(max_length=10, null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='license',
            field=models.CharField(max_length=100, null=True, db_index=True),
        ),
    ]
