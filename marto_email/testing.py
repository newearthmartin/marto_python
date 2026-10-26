import django

DB_BACKEND = 'marto_email.backend.DBEmailBackend'
STACKED_BACKEND = 'marto_email.backend.StackedEmailBackend'


def db_layer(**options):
    return {'BACKEND': DB_BACKEND, 'OPTIONS': options}


def mailer_settings(stack, **mailers):
    """
    Settings for `self.settings(**...)` making the given stack (innermost first) the default mailer, as
    Django 6.1's MAILERS or, before it, the global EMAIL_BACKEND_STACK. `mailers` adds other aliases (6.1 only).
    """
    if django.VERSION < (6, 1):
        return {'EMAIL_BACKEND': STACKED_BACKEND, 'EMAIL_BACKEND_STACK': stack}
    mailers['default'] = stack
    return {'MAILERS': {alias: {'BACKEND': STACKED_BACKEND, 'OPTIONS': {'stack': alias_stack}}
                        for alias, alias_stack in mailers.items()}}
