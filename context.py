from django.conf import settings
from django.contrib.sites.models import RequestSite

def messageContextProcessor(request):
    if request.session.has_key('messages'):
        messages = request.session['messages']
        request.session['messages'] = None
        return {'messages': messages}
    else:
        return {}

def settingsContextProcessor(request):
    return {'settings':settings}

def siteContextProcessor(request):
    return {'site': RequestSite(request)}

def currentPathContextProcessor(request):
    return {'current_path': request.get_full_path()}
