DB_BACKEND = 'marto_email.backend.DBEmailBackend'
STACKED_BACKEND = 'marto_email.backend.StackedEmailBackend'


def db_layer(**options):
    return {'BACKEND': DB_BACKEND, 'OPTIONS': options}


def mailer_settings(stack, **mailers):
    """
    Settings for `self.settings(**...)` making the given stack (innermost first) the default mailer.
    `mailers` adds other aliases, each with its own stack.
    """
    mailers['default'] = stack
    return {'MAILERS': {alias: {'BACKEND': STACKED_BACKEND, 'OPTIONS': {'stack': alias_stack}}
                        for alias, alias_stack in mailers.items()}}
