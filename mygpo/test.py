import os.path

from django.conf import settings

from couchdbkit import Database
from couchdbkit.loaders import FileSystemDocsLoader
from couchdbkit.ext.django.testrunner import CouchDbKitTestSuiteRunner

from mygpo.db.couchdb.utils import sync_design_docs


# inspired by
# http://djangosnippets.org/snippets/2211/

class MygpoTestSuiteRunner(CouchDbKitTestSuiteRunner):
    """
    Test runner that is able to skip some tests according to settings.py
    """

    def __init__(self, *args, **kwargs):
        self.EXCLUDED_APPS = getattr(settings, 'TEST_EXCLUDE', [])
        settings.TESTING = True
        super(MygpoTestSuiteRunner, self).__init__(*args, **kwargs)


    def setup_databases(self, **kwargs):
        ret = super(MygpoTestSuiteRunner, self).setup_databases(**kwargs)
        sync_design_docs()
        return ret


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


def create_auth_string(username, password):
    import base64
    credentials = base64.encodestring("%s:%s" % (username, password)).rstrip()
    auth_string = 'Basic %s' % credentials
    return auth_string
