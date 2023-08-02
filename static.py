import django.contrib.staticfiles.handlers as staticfiles_handlers


def setup_cors_static_file_handler():
    """
    Changes the static files handler to add Access-Control-Allow-Origin to static files.
    Call from (dev) settings
    """
    class CORSStaticFilesHandler(staticfiles_handlers.StaticFilesHandler):
        def serve(self, request):
            response = super().serve(request)
            response['Access-Control-Allow-Origin'] = '*'
            return response
    staticfiles_handlers.StaticFilesHandler = CORSStaticFilesHandler
