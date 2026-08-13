import json
import logging
import time
from datetime import datetime, timedelta
from functools import wraps

from celery import shared_task, signature, current_task
from celery.result import AsyncResult
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from threading import Thread
from redlock.lock import RedLockError
from marto_python.redis import get_redis, get_redis_key, get_signature_redis_key, redis_lock
from marto_python.strings import cut_str


logger = logging.getLogger(__name__)


MAX_TRACK_SECONDS = 10
TASK_LOCK_TTL = 5 * 60 * 1000


def track_task_view(request):
    # TODO:
    # This is a fast view method for getting the result of a task, but there is no security check
    #  that the caller of this method is the one that submitted the task.
    task_id = request.GET.get('task_id', None)
    if not task_id:
        return HttpResponseBadRequest()
    response = track_task_loop(task_id)
    return JsonResponse(response)


def track_task_loop(task_id, max_seconds=MAX_TRACK_SECONDS):
    task = AsyncResult(task_id)
    now = datetime.now()
    while (datetime.now() - now).seconds < max_seconds:
        if task.successful():
            return task.get()
        elif task.failed():
            return {'error': f'Error executing background task {task_id}'}
        time.sleep(0.1)
    return {'task_id': task_id}


def task_only_one(*decorator_args, **decorator_kwargs):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            redis_key = 'only_one.' + get_redis_key(fn, *args, **kwargs)
            task_id_key = f'{redis_key}.task_id'
            try:
                with redis_lock(redis_key, *decorator_args, **decorator_kwargs):
                    redis = get_redis()
                    task_id = current_task.request.id
                    ttl = decorator_kwargs.get('ttl')
                    if task_id:
                        if ttl:
                            redis.set(task_id_key, task_id, px=ttl)
                        else:
                            redis.set(task_id_key, task_id)
                    try:
                        return fn(*args, **kwargs)
                    finally:
                        if task_id:
                            redis.delete(task_id_key)
            except RedLockError:
                logger.warning(f'Task {redis_key} already being executed.')
                active_task_id = get_redis().get(task_id_key)
                if active_task_id:
                    if isinstance(active_task_id, bytes):
                        active_task_id = active_task_id.decode()
                    return {'task_id': active_task_id}
                return {'task_already': True}
        return wrapper
    return decorator


@shared_task
def debounce_task(sig, seconds=60, debounced=False):
    if type(sig) is not dict:  # Converting it to dict to get the same signature in sync and async call
        sig = json.loads(json.dumps(sig))

    redis_key = 'debounce.' + get_signature_redis_key(sig)
    log_key = cut_str(redis_key, 200)
    redis = get_redis()

    if seconds != 0:
        ts = redis.get(redis_key)

        if not debounced or ts is None:
            debounce_ts = timezone.now() + timedelta(seconds=seconds)
            logger.info(f'debounce - waiting {seconds} secs - {log_key}.')
            redis.set(redis_key, int(debounce_ts.timestamp()))
            debounce_task.apply_async([sig], {'seconds': seconds, 'debounced': True}, countdown=seconds)
            return

        if timezone.now() < datetime.fromtimestamp(int(ts), tz=timezone.get_current_timezone()):
            logger.info(f'debounce - not yet - {log_key}.')
            return

    if seconds == 0:
        logger.info(f'debounce - seconds is 0 - executing immediately - {log_key}')
    else:
        logger.info(f'debounce - executing - {log_key}')
    redis.delete(redis_key)
    signature(sig).apply_async()


class CeleryOrThread:
    """
    Decorator that
    - runs the task in celery as delay if USE_CELERY == True
    - or else runs in thread.
    """
    def __init__(self, f):
        self.f = f

    def sync_call(self, *args, **kwargs):
        self.f(*args, **kwargs)

    def async_call(self, *args, **kwargs):
        self.__call__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if settings.USE_CELERY:
            task = self.f.delay(*args, **kwargs)
            return task
        else:
            Thread(target=lambda: self.f(*args, **kwargs)).start()
            return None


@shared_task
def hola():
    logger.info("hola!!! :)")
    return 7


@shared_task
def hola_error():
    my_list = []
    logger.error("my error")
    my_list[0] = 0  # trigger an exception


@shared_task
def test_mail():
    EmailMessage(
        'Testing email from celery task',
        'Email message body',
        to=[email for _, email in settings.ADMINS]
    ).send()
