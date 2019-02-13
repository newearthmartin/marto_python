from django.conf import settings


# noinspection PyMethodMayBeStatic
class FirstTimeCookieMiddleware(object):

    def process_request(self, request):
        request.siteCookie = settings.SITE_COOKIE_NAME in request.COOKIES

    def process_response(self, _, response):
        response.set_cookie(settings.SITE_COOKIE_NAME)
        return response
