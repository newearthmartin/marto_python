from django.conf import settings
from django.core.servers import basehttp
from django.core.management.commands.runserver import Command as BaseCommand


class QuietWSGIRequestHandler(basehttp.WSGIRequestHandler):
    def log_message(self, the_format, *args):
        # Don't bother logging requests for paths under MEDIA_URL.
        if self.path.startswith(settings.MEDIA_URL) or self.path.startswith(settings.STATIC_URL):
            return
        # can't use super as base is old-style class, so call method explicitly
        return super(QuietWSGIRequestHandler, self).log_message(the_format, *args)


def run(addr, port, wsgi_handler):
    server_address = (addr, port)
    httpd = basehttp.WSGIServer(server_address, QuietWSGIRequestHandler)
    httpd.set_app(wsgi_handler)
    httpd.serve_forever()


class Command(BaseCommand):
    def handle(self, addrport='', *args, **options):
        """
        # monkeypatch Django to use our quiet server
        basehttp.run = run
        return super(Command, self).handle(addrport, *args, **options)
        """
        run('localhost', 8000, None)
