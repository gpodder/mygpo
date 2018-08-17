# -*- coding: utf-8 -*-


from django.db import models, migrations
import mygpo.users.models
import mygpo.utils


class Migration(migrations.Migration):

    dependencies = [('auth', '__first__'), ('users', '0005_auto_20140719_1105')]

    operations = [
        migrations.CreateModel(
            name='UserProxy', fields=[], options={'proxy': True}, bases=('auth.user',)
        ),
        migrations.AlterField(
            model_name='client',
            name='uid',
            field=models.CharField(
                max_length=64, validators=[mygpo.users.models.UIDValidator()]
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='favorite_feeds_token',
            field=models.CharField(
                default=mygpo.utils.random_token, max_length=32, null=True
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='publisher_update_token',
            field=models.CharField(
                default=mygpo.utils.random_token, max_length=32, null=True
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='subscriptions_token',
            field=models.CharField(
                default=mygpo.utils.random_token, max_length=32, null=True
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='userpage_token',
            field=models.CharField(
                default=mygpo.utils.random_token, max_length=32, null=True
            ),
        ),
    ]
