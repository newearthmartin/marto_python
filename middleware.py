from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django.template import RequestContext, loader


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
    def process_view(self, request, view_func, view_args, view_kwargs):
        template = loader.get_template('maintenance.html')
        request_context = RequestContext(request, {}, processors=[])
        return HttpResponse(template.template.render(request_context), status=503)
