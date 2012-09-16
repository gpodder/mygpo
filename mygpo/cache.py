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

            key = create_key(f.func_name, args, kwargs)

            get_kwargs = dict(cache_kwargs)
            get_kwargs.pop('timeout')
            value = cache.get(key, NOT_IN_CACHE, **get_kwargs)

            if value is NOT_IN_CACHE:
                value = f(*args, **kwargs)

                cache.set(key, value, **cache_kwargs)

            return value


        return _get

    return _wrapper



def create_key(key, args, kwargs):

    args_str = '-'.join(str(hash(a)) for a in args)
    kwargs_str = '-'.join(str(hash(i)) for i in kwargs.items())

    return '{key}-{args}-{kwargs}'.format(key=key, args=hash(args_str),
            kwargs=hash(kwargs_str))
