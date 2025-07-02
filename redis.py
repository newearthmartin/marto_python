from redis import Redis
from django.conf import settings
from redlock.lock import RedLockFactory


__redis = None
__redlock_factory = None


def get_redis():
    global __redis
    if not __redis:
        __redis = Redis(port=settings.REDIS_PORT)
    return __redis


def redis_lock(lock_name, *args, **kwargs):
    global __redlock_factory
    if not __redlock_factory:
        __redlock_factory = RedLockFactory([{'host': 'localhost', 'port': settings.REDIS_PORT}])
    return __redlock_factory.create_lock(lock_name, *args, **kwargs)


def get_redis_key(fn, *args, **kwargs):
    return f'{fn.__module__}.{fn.__name__}-{args}{kwargs}'
