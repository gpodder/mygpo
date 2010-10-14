from django.test.simple import DjangoTestSuiteRunner
from django.conf import settings

# inspired by
# http://djangosnippets.org/snippets/2211/

class MygpoTestSuiteRunner(DjangoTestSuiteRunner):
    """
    Test runner that doesn't create or destroy a test database (it requires
    a pre-setup database), and is able to skip some tests according to
    settings.py
    """

    def __init__(self, *args, **kwargs):
        self.EXCLUDED_APPS = getattr(settings, 'TEST_EXCLUDE', [])
        settings.TESTING = True
        super(MygpoTestSuiteRunner, self).__init__(*args, **kwargs)


    def build_suite(self, *args, **kwargs):
        suite = super(MygpoTestSuiteRunner, self).build_suite(*args, **kwargs)
        if not args[0] and not getattr(settings, 'RUN_ALL_TESTS', False):
            tests = []
            for case in suite:
                pkg = case.__class__.__module__.split('.')[0]
                if pkg not in self.EXCLUDED_APPS:
                    tests.append(case)
            suite._tests = tests
        return suite


    def setup_databases(*args, **kwargs):
        from django.db import connections
        old_names = []
        mirrors = []
        for alias in connections:
            connection = connections[alias]
            # If the database is a test mirror, redirect it's connection
            # instead of creating a test database.
            if connection.settings_dict['TEST_MIRROR']:
                mirrors.append((alias, connection))
                mirror_alias = connection.settings_dict['TEST_MIRROR']
                connections._connections[alias] = connections[mirror_alias]
            else:
                old_names.append((connection, connection.settings_dict['NAME']))

                # don't create a test-database, because we require
                # a pre-existing one
                connection.creation.connection.settings_dict['NAME'] = \
                    'test_' + connection.creation.connection.settings_dict['NAME']
                connection.creation.connection.features.confirm()
                #connection.creation.create_test_db(self.verbosity, autoclobber=not self.interactive)

        return old_names, mirrors

    def teardown_databases(*args, **kwargs):
        pass

def create_auth_string(username, password):
    import base64
    credentials = base64.encodestring("%s:%s" % (username, password)).rstrip()
    auth_string = 'Basic %s' % credentials
    return auth_string
