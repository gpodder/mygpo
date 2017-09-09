# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.UUIDField(
                    max_length=32,
                    serialize=False,
                    primary_key=True)),
                ('uid', models.CharField(max_length=64)),
                ('name', models.CharField(
                    default='New Device',
                    max_length=100)),
                ('type', models.CharField(
                    default='other',
                    max_length=7,
                    choices=[
                        ('desktop', 'Desktop'),
                        ('laptop', 'Laptop'),
                        ('mobile', 'Cell phone'),
                        ('server', 'Server'),
                        ('tablet', 'Tablet'),
                        ('other', 'Other')])),
                ('deleted', models.BooleanField(default=False)),
                ('user_agent', models.CharField(max_length=300)),
                ('user', models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    on_delete=models.CASCADE,
                )),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='client',
            unique_together=set([('user', 'uid')]),
        ),
    ]
