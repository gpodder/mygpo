# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0002_pluralname'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historyentry',
            options={'ordering': [b'-timestamp'], 'verbose_name_plural': b'History Entries'},
        ),
        migrations.AlterField(
            model_name='historyentry',
            name='action',
            field=models.CharField(max_length=11, choices=[(b'subscribe', b'subscribed'), (b'unsubscribe', b'unsubscribed'), (b'flattr', b"flattr'd")]),
        ),
        migrations.AlterField(
            model_name='historyentry',
            name='client',
            field=models.ForeignKey(to='users.Client', null=True),
        ),
    ]
