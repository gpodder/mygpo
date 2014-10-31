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

except ImportError:
    print('ujson not found', file=sys.stderr)

    try:
        # If SimpleJSON is installed separately, it might be a recent version
        import simplejson as json
        JSONDecodeError = json.JSONDecodeError

    except ImportError:
        print('simplejson not found', file=sys.stderr)

        # Otherwise use json from the stdlib
        from . import json
        JSONDecodeError = ValueError
