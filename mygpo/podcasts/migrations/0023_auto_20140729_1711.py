# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [('podcasts', '0022_index_episode_listeners'), ('auth', '__first__')]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='user',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='episode',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='podcast',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set(
                [('tag', 'source', 'user', 'content_type', 'object_id')]
            ),
        ),
    ]
