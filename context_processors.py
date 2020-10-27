import logging

from django.conf import settings as the_settings
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
