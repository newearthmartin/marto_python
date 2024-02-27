from redis import Redis
from django.conf import settings


def get_redis():
    return Redis(port=settings.REDIS_PORT)
