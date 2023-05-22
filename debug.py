from django.conf import settings
from django.urls import path, include

use_debug_toolbar = False


def setup_debug_toolbar(installed_apps, middleware):
    global use_debug_toolbar
    use_debug_toolbar = True
    installed_apps.append('debug_toolbar')
    middleware.append('debug_toolbar.middleware.DebugToolbarMiddleware')


def add_debug_toolbar_if_enabled(urlpatterns):
    if use_debug_toolbar:
        import debug_toolbar
        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]

