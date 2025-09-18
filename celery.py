import json
import logging
from datetime import datetime, timedelta
from celery import shared_task, signature
from celery.utils.log import get_task_logger
from django.utils import timezone
from marto_python.redis import get_redis, get_signature_redis_key
from marto_python.strings import cut_str
from marto_python.email.email import send_email_to_admins


logger = logging.getLogger(__name__)


@shared_task
def debounce_task(sig, seconds=60, debounced=False):
    if type(sig) is not dict:  # Converting it to dict to get the same signature in sync and async call
        sig = json.loads(json.dumps(sig))

    redis_key = 'debounce.' + get_signature_redis_key(sig)
    log_key = cut_str(redis_key, 200)
    redis = get_redis()

    ts = redis.get(redis_key)

    if not debounced or ts is None:
        debounce_ts = timezone.now() + timedelta(seconds=seconds)
        logger.info(f'debounce - waiting {seconds} secs - {log_key}.')
        redis.set(redis_key, str(debounce_ts.timestamp()))
        debounce_task.apply_async([sig], {'seconds': seconds, 'debounced': True}, countdown=seconds)
        return

    if timezone.now() < datetime.fromtimestamp(float(ts), tz=timezone.get_current_timezone()):
        logger.info(f'debounce - not yet - {log_key}.')
        return

    logger.info(f'debounce - executing - {log_key}')
    redis.delete(redis_key)
    signature(sig).apply_async()


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
    send_email_to_admins('Testing email from celery task', 'Email message body')
