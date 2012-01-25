#
# Tries to import the best JSON module available
#

import sys


try:
    # UltraJSON should be the fastest
    # get it from
    # https://github.com/esnme/ultrajson
    # http://pypi.python.org/pypi/ujson/
    import ujson as json
    JSONDecodeError = ValueError

except:
    print >> sys.stderr, 'ujson not found'

    try:
        # If SimpleJSON is installed separately, it might be a recent version
        import simplejson as json
        JSONDecodeError = json.JSONDecodeError

    except:
        print >> sys.stderr, 'simplejson not found'

        # Otherwise use json from the stdlib
        import json
        JSONDecodeError = ValueErro
