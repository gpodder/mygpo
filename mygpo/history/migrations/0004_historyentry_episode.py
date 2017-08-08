# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0003_historyentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='historyentry',
            name='episode',
            field=models.ForeignKey(
                to='podcasts.Episode',
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
    ]
