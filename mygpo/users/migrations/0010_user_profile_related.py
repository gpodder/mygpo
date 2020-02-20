# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [('users', '0009_user_unique_email')]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(
                related_name='profile',
                to=settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
            ),
        )
    ]
