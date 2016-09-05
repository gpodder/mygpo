from django.db import migrations


def forward(apps, schema_editor):

    # This index can apparently not be created on sqlite
    # As it is not recommended for production use, we can just
    # skip the index there
    if schema_editor.connection.vendor == 'sqlite':
        return

    migrations.RunSQL(
        sql=[
            ('CREATE UNIQUE INDEX user_case_insensitive_unique '
             'ON auth_user ((lower(username)));', None),
        ],
    )


def reverse(apps, schema_editor):
    migrations.RunSQL([
        ('DROP INDEX IF EXISTS user_case_insensitive_unique', None),
    ])


class Migration(migrations.Migration):
    """ Create a unique case-insensitive index on the username column """

    dependencies = [
        ('auth', '0001_initial'),
        ('users', '0014_django_uuidfield'),
    ]

    operations = [
        # Wrap RunSQL in RunPython to check for DB backend
        # http://stackoverflow.com/a/37521148/693140
        migrations.RunPython(
            code=forward,
            reverse_code=reverse,
        )
    ]
