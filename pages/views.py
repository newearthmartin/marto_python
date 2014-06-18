from django.template.context import RequestContext
from django.http.response import Http404
from django.shortcuts import render_to_response

def page(request,url):
    request_context = RequestContext(request)
    if not request_context.has_key('page') or not request_context['page']:
        raise Http404
    return render_to_response('page.html', {}, request_context)

