from django.conf import settings
from django.middleware.csrf import CSRF_SESSION_KEY

# noinspection PyMethodMayBeStatic
class FirstTimeCookieMiddleware(object):

    def process_request(self, request):
        request.siteCookie = settings.SITE_COOKIE_NAME in request.COOKIES

    def process_response(self, _, response):
        response.set_cookie(settings.SITE_COOKIE_NAME)
        return response

def get_CSRF_token(request):
    if settings.USE_CSRF_SESSIONS:
        return request.session.get(CSRF_SESSION_KEY, None)
    else:
        return request.COOKIES.get(settings.CSRF_COOKIE_NAME, None)