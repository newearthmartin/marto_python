from redis import Redis
from django.conf import settings
from redlock.lock import RedLock, RedLockFactory


def get_redis():
    return Redis(port=settings.REDIS_PORT)


def redis_lock(lock_name, *args, **kwargs):
    redis_connection = [{'host': 'localhost', 'port': settings.REDIS_PORT}]
    return RedLock(lock_name, redis_connection, *args, **kwargs)
