from hashlib import sha1
from django.core.cache import cache
from functools import wraps


NOT_IN_CACHE = object()


def cache_result(**cache_kwargs):
    """ Decorator to cache the result of a function call

    Usage

    @cache_result('myfunc', timeout=60)
    def my_function(a, b, c):
        pass
    """

    def _wrapper(f):

        @wraps(f)
        def _get(*args, **kwargs):

            key = sha1(str(f.__module__) + str(f.__name__) +
                       unicode(args) + unicode(kwargs)).hexdigest()

            # the timeout parameter can't be used when getting from a cache
            get_kwargs = dict(cache_kwargs)
            get_kwargs.pop('timeout', None)

            value = cache.get(key, NOT_IN_CACHE, **get_kwargs)

            if value is NOT_IN_CACHE:
                value = f(*args, **kwargs)

                cache.set(key, value, **cache_kwargs)

            return value

        return _get

    return _wrapper
