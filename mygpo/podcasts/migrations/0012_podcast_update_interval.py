# encoding: utf8


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0011_auto_20140614_1241'),
    ]

    operations = [
        migrations.AddField(
            model_name='podcast',
            name='update_interval',
            field=models.PositiveSmallIntegerField(default=168),
            preserve_default=True,
        ),
    ]
