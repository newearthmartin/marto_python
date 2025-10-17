def configure_debug_toolbar(installed_apps, middleware):
    installed_apps.append('debug_toolbar')
    middleware.append('debug_toolbar.middleware.DebugToolbarMiddleware')


def add_debug_toolbar_urls(urlpatterns):
    from django.urls import path, include  # importing here to prevent circular imports
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
