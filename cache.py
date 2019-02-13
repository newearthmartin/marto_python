from django.core.cache import caches


class CacheDecorator:
    def __init__(self, cache_key, timeout=60*10, cache_name='default'):
        self.cache_key = cache_key
        self.timeout = timeout
        self.cache_name = cache_name

    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            cache = caches[self.cache_name]
            retval = cache.get(self.cache_key)
            if not retval:
                retval = f(*args, **kwargs)
                cache.set(self.cache_key, retval, self.timeout)
            return retval
        return wrapped_f
