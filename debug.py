from django.urls import path, include

debug_toolbar_enabled = False


def enable_debug_toolbar(installed_apps, middleware):
    global debug_toolbar_enabled
    debug_toolbar_enabled = True
    installed_apps.append('debug_toolbar')
    middleware.append('debug_toolbar.middleware.DebugToolbarMiddleware')


def add_debug_toolbar_if_enabled(urlpatterns):
    if debug_toolbar_enabled:
        import debug_toolbar
        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]

