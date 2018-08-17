# encoding: utf8


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('podcasts', '0009_auto_20140614_1231')]

    operations = [
        migrations.AlterField(
            model_name='podcast',
            name='author',
            field=models.CharField(max_length=250, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='author',
            field=models.CharField(max_length=250, null=True, blank=True),
        ),
    ]
