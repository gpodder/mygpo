# encoding: utf8


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [('podcasts', '0016_restrictions_notnull')]

    operations = [
        migrations.AlterField(
            model_name='podcast',
            name='author',
            field=models.CharField(max_length=350, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='author',
            field=models.CharField(max_length=350, null=True, blank=True),
        ),
    ]
