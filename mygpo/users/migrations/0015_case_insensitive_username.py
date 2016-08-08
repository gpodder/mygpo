from django.db import migrations


class Migration(migrations.Migration):
    """ Create a unique case-insensitive index on the username column """

    dependencies = [
        ('auth', '0001_initial'),
        ('users', '0014_django_uuidfield'),
    ]

    operations = [
        migrations.RunSQL(
            'CREATE UNIQUE INDEX user_case_insensitive_unique '
            'ON auth_user ((lower(username)));',
            'DROP INDEX user_case_insensitive_unique',
        ),
    ]
