from .util import is_function

def foreign_field(field_name):
    def accessor(obj):
        val = obj
        for part in field_name.split('__'):
            val = getattr(val, part)
        return val if not is_function(val) else val()
    accessor.__name__ = field_name

    return accessor


ff = foreign_field