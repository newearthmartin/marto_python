def foreign_field(field_name):
    def accessor(obj):
        val = obj
        for part in field_name.split('__'):
            val = getattr(val, part)
        return val
    accessor.__name__ = field_name
    return accessor


ff = foreign_field