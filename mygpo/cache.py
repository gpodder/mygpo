from django.core.cache import cache


NOT_IN_CACHE = object()


def get_cache_or_calc(key, calc, timeout=None, version=None, *args, **kwargs):
    """ Gets the value from the cache or calculates it

    If the value needs to be calculated, it is stored in the cache. """

    value = cache.get(key, NOT_IN_CACHE, version=version)

    if value is NOT_IN_CACHE:
        value = calc(*args, **kwargs)
        cache.set(key, value, timeout=timeout, version=version)

    return value



def cache_result(key, timeout=None, version=None):
    """ Decorator to cache the result of a function call

    Usage

    @cache_result('myfunc', timeout=60)
    def my_function(a, b, c):
        pass
    """

    def _wrapper(f):

        def _get(*args, **kwargs):

            key = create_key(key, args, kwargs)
            key = 'a'

            value = cache.get(key, NOT_IN_CACHE, version=version)

            if value is NOT_IN_CACHE:
                value = f(*args, **kwargs)

                cache.set(key, value, timeout=timeout, version=version)

            return value


        return _get

    return _wrapper



def create_key(key, args, kwargs):

    args_str = '-'.join(hash(a) for a in args)
    kwargs_str = '-'.join(hash(i) for i in kwargs.items())

    return '{key}-{args}-{kwargs}'.format(key=key, args=hash(args_str),
            kwargs=hash(kwargs_str))
