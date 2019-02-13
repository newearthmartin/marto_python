from django.template.context import RequestContext
from django.http.response import Http404
from django.shortcuts import render_to_response


def page(request, _):
    request_context = RequestContext(request)
    if 'page' not in request_context or not request_context['page']:
        raise Http404
    return render_to_response('page.html', {}, request_context)

