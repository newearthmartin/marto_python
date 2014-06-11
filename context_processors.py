from django.conf import settings as the_settings
from django.contrib.sites.models import RequestSite
from marto_python.util import is_site_view

def site_view_only(func):
    def inner(request):
        if not is_site_view(request.path):
            return {}
        else:
            return func(request)
    return inner

@site_view_only
def messages(request):
    #print 'MESSAGES CONTEXT PROCESSOR', request.path
    if request.session.has_key('messages'):
        msgs = request.session['messages']
        request.session['messages'] = None
        return {'messages': msgs}
    else:
        return {}

@site_view_only
def settings(request):
    #print 'SETTINGS CONTEXT PROCESSOR', request.path
    return {'settings':the_settings}

@site_view_only
def site(request):
    #print 'SITE CONTEXT PROCESSOR', request.path
    return {'site': RequestSite(request)}

@site_view_only
def current_path(request):
    #print 'CURRENT_PATH CONTEXT PROCESSOR', request.path
    return {'current_path': request.get_full_path()}
