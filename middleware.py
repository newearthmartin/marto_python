from django.utils.deprecation import MiddlewareMixin


class ViewShortcutMiddleware(MiddlewareMixin):
    def __init__(self, get_response, view_fns):
        super().__init__(get_response)
        self.view_fns = set(view_fns)
    def process_view(self, request, view_func, view_args, view_kwargs):
        if view_func in self.view_fns:
            return view_func(request, *view_args, **view_kwargs)
        return None
