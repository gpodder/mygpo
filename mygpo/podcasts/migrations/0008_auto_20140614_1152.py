# encoding: utf8


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0007_auto_20140614_0846'),
    ]

    operations = [
        migrations.AlterField(
            model_name='podcast',
            name='subtitle',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='podcastgroup',
            name='subtitle',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='subtitle',
            field=models.TextField(blank=True),
        ),
    ]
