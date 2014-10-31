# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings
import uuidfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', uuidfield.fields.UUIDField(max_length=32, serialize=False, primary_key=True)),
                ('uid', models.CharField(max_length=64)),
                ('name', models.CharField(default=b'New Device', max_length=100)),
                ('type', models.CharField(default=b'other', max_length=7, choices=[(b'desktop', 'Desktop'), (b'laptop', 'Laptop'), (b'mobile', 'Cell phone'), (b'server', 'Server'), (b'tablet', 'Tablet'), (b'other', 'Other')])),
                ('deleted', models.BooleanField(default=False)),
                ('user_agent', models.CharField(max_length=300)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='client',
            unique_together=set([(b'user', b'uid')]),
        ),
    ]
