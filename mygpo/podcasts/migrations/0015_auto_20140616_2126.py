# encoding: utf8


from django.db import models, migrations


def set_scope(apps, schema_editor):
    URL = apps.get_model('podcasts', 'URL')
    Slug = apps.get_model('podcasts', 'Slug')

    URL.objects.filter(scope__isnull=True).update(scope='')
    Slug.objects.filter(scope__isnull=True).update(scope='')


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0014_auto_20140615_1032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slug',
            name='scope',
            field=models.CharField(db_index=True, max_length=32, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='url',
            name='scope',
            field=models.CharField(db_index=True, max_length=32, blank=True, null=True),
        ),
        migrations.RunPython(set_scope),
        migrations.AlterField(
            model_name='slug',
            name='scope',
            field=models.CharField(db_index=True, max_length=32, blank=True, null=False),
        ),
        migrations.AlterField(
            model_name='url',
            name='scope',
            field=models.CharField(db_index=True, max_length=32, blank=True, null=False),
        ),

    ]
