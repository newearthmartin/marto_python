from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.conf import settings


class ViewShortcutMiddleware(MiddlewareMixin):
    def __init__(self, get_response, view_fns):
        super().__init__(get_response)
        self.view_fns = set(view_fns)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if view_func in self.view_fns:
            return view_func(request, *view_args, **view_kwargs)
        return None


# noinspection PyMethodMayBeStatic
class MaintenanceMiddleware(MiddlewareMixin):
    def is_exempt(self, request, view_fn, view_args, view_kwargs):
        if request.path.startswith('/admin/'): return True
        if (static_url := getattr(settings, 'STATIC_URL', None)) and request.path.startswith(static_url): return True
        if (media_url := getattr(settings, 'MEDIA_URL', None)) and request.path.startswith(media_url): return True
        return False

    def process_view(self, request, view_func, view_args, view_kwargs):
        if self.is_exempt(request, view_func, view_args, view_kwargs): return None
        template = loader.get_template('maintenance.html')
        request_context = RequestContext(request, {}, processors=[])
        return HttpResponse(template.template.render(request_context), status=503)
