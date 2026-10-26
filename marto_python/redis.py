from contextlib import contextmanager

from redis import Redis
from redis.exceptions import LockError
from django.conf import settings


__redis = None

DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DB = 0
DEFAULT_LOCK_TTL = 100 * 1000
LOCK_WAIT_SECONDS = 0.5
LOCK_RETRY_SECONDS = 0.1


class RedisLockError(Exception):
    pass


def get_redis():
    global __redis
    if not __redis:
        __redis = Redis(
            port=getattr(settings, 'REDIS_PORT', DEFAULT_REDIS_PORT),
            db=getattr(settings, 'REDIS_DB', DEFAULT_REDIS_DB))
    return __redis


@contextmanager
def redis_lock(lock_name, ttl=DEFAULT_LOCK_TTL):
    """Hold the Redis lock `lock_name` (expiring after `ttl` ms) for the block.

    Waits briefly for a lock another holder has, then raises RedisLockError.
    """
    lock = get_redis().lock(lock_name, timeout=ttl / 1000, blocking_timeout=LOCK_WAIT_SECONDS,
                            sleep=LOCK_RETRY_SECONDS)
    if not lock.acquire():
        raise RedisLockError(f'failed to acquire lock {lock_name}')
    try:
        yield
    finally:
        try:
            lock.release()
        except LockError:  # expired while held; the next holder owns it now
            pass


def get_redis_key(fn, *args, **kwargs):
    return f'{fn.__module__}.{fn.__name__}-{args}{kwargs}'


def get_signature_redis_key(sig):
    return f'{sig["task"]}-{sig["args"]}{sig["kwargs"]}'
