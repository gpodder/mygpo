# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0002_pluralname'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historyentry',
            options={'ordering': ['-timestamp'], 'verbose_name_plural': 'History Entries'},
        ),
        migrations.AlterField(
            model_name='historyentry',
            name='action',
            field=models.CharField(max_length=11, choices=[('subscribe', 'subscribed'), ('unsubscribe', 'unsubscribed'), ('flattr', "flattr'd")]),
        ),
        migrations.AlterField(
            model_name='historyentry',
            name='client',
            field=models.ForeignKey(to='users.Client', null=True),
        ),
    ]
