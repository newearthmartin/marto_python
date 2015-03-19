from django.core.cache import get_cache

class cache_decorator:
    def __init__(self, cache_key, timeout=60*10, cache_name='default'):
        self.cache_key = cache_key
        self.timeout = timeout
        self.cache_name = cache_name
    def __call__(self, f, *args, **kwargs):
        cache = get_cache(self.cache_name)
        retval = cache.get(self.cache_key)
        if not retval:
            retval = f(*args, **kwargs)
            cache.set(self.cache_key, retval, self.timeout)
        return retval
