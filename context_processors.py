import logging

from django.conf import settings as the_settings
from django.contrib.sites.requests import RequestSite
from marto_python.util import is_site_view

logger = logging.getLogger(__name__)


def site_view_only(func):
    def inner(request):
        return func(request) if is_site_view(request.path) else {}
    return inner


@site_view_only
def messages(request):
    logger.debug(f'MESSAGES CONTEXT PROCESSOR {request.path}')
    if 'messages' in request.session:
        msgs = request.session['messages']
        request.session['messages'] = None
        return {'messages': msgs}
    else:
        return {}


@site_view_only
def settings(request):
    logger.debug(f'SETTINGS CONTEXT PROCESSOR {request.path}')
    return {'settings': the_settings}


@site_view_only
def site(request):
    logger.debug(f'SITE CONTEXT PROCESSOR {request.path}')
    return {'site': RequestSite(request)}


@site_view_only
def current_path(request):
    logger.debug(f'CURRENT_PATH CONTEXT PROCESSOR {request.path}')
    return {'current_path': request.get_full_path()}
