import logging

from django.conf import settings as the_settings
from django import contrib
from django.contrib.sites.requests import RequestSite
from marto_python.util import is_site_view
from marto_python.url import get_server_url

logger = logging.getLogger(__name__)


def site_view_only(func):
    def inner(request):
        return func(request) if is_site_view(request.path) else {}
    return inner


@site_view_only
def messages(request):
    if 'messages' in request.session:
        msgs = request.session['messages']
        request.session['messages'] = None
        return {'messages': msgs}
    else:
        return {}


def get_contrib_messages_data(request):
    msgs = contrib.messages.get_messages(request)
    rv = []
    for msg in msgs:
        rv.append({
            'message': msg.message,
            'level': msg.level,
            'level_tag': msg.level_tag,
            'tags': msg.tags,
            'extra_tags': msg.extra_tags,
        })
    return rv


@site_view_only
def contrib_messages_data(request):
    return {'messages_data': get_contrib_messages_data(request)}


@site_view_only
def settings(request):
    return {'settings': the_settings}


@site_view_only
def site(request):
    return {
        'site': RequestSite(request),
        'server_url': get_server_url(),
    }


@site_view_only
def current_path(request):
    return {'current_path': request.get_full_path()}
