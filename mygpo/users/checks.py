from django.core.checks import register, Warning
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError


SQL = """
SELECT count(*), lower(username)
FROM auth_user
GROUP BY lower(username)
HAVING count(*) > 1;
"""


@register()
def check_case_insensitive_users(app_configs=None, **kwargs):
    errors = []

    try:
        cursor = connection.cursor()
        cursor.execute(SQL)
        non_unique = cursor.fetchall()

        usernames = [t[1] for t in non_unique]

        if len(non_unique) > 0:
            txt = 'There are {0} non-unique usernames: {1}'.format(
                len(non_unique), ', '.join(usernames[:10] + ['...'])
            )
            wid = 'users.W001'
            errors.append(Warning(txt, id=wid))

    except OperationalError as oe:
        if 'no such table: auth_user' in str(oe):
            # Ignore if the table does not yet exist, eg when initally
            # running ``manage.py migrate``
            pass
        else:
            raise

    except ProgrammingError as pe:
        if 'relation "auth_user" does not exist' in str(pe):
            # Ignore if the table does not yet exist, eg when initally
            # running ``manage.py migrate``
            pass
        else:
            raise

    return errors
