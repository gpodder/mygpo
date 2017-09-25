# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0028_episode_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExamplePodcast',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('order', models.PositiveSmallIntegerField()),
                ('podcast', models.ForeignKey(
                    to='podcasts.Podcast',
                    on_delete=models.CASCADE,
                )),
            ],
            options={
                'ordering': ['order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='examplepodcast',
            unique_together=set([('order',)]),
        ),
    ]
