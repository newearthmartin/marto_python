from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import render


class ViewShortcutMiddleware(MiddlewareMixin):
    def __init__(self, get_response, view_fns):
        super().__init__(get_response)
        self.view_fns = set(view_fns)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if view_func in self.view_fns:
            return view_func(request, *view_args, **view_kwargs)
        return None


class TemplateMiddleware(MiddlewareMixin):
    def __init__(self, get_response, template, status_code=None):
        super().__init__(get_response)
        self.template = template
        self.status_code = status_code

    def process_view(self, request, view_func, view_args, view_kwargs):
        return render(request, self.template, {}, status=self.status_code)


class MaintenanceMiddleware(TemplateMiddleware):
    def __init__(self, get_response):
        super().__init__(get_response, 'maintenance.html', status_code=503)