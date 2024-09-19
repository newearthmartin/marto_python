from redis import Redis
from django.conf import settings
from redlock.lock import RedLock, RedLockFactory


def get_redis():
    return Redis(port=settings.REDIS_PORT)


__redlock_factory = None


def redis_lock(lock_name, *args, **kwargs):
    global __redlock_factory
    if not __redlock_factory:
        __redlock_factory = RedLockFactory([{'host': 'localhost', 'port': settings.REDIS_PORT}])
    return __redlock_factory.create_lock(lock_name, *args, **kwargs)
