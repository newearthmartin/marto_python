from django.contrib.admin import SimpleListFilter
from .util import is_function


def foreign_field(field_name):
    def accessor(obj):
        val = obj
        for part in field_name.split('__'):
            val = getattr(val, part)
        return val if not is_function(val) else val()
    accessor.__name__ = field_name

    return accessor


class YesNoFilter(SimpleListFilter):
    def lookups(self, request, model_admin):
        return [
            ('1', 'yes'),
            ('0', 'no'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            queryset = self.queryset_yes_no(request, queryset, self.value() == '1')
        return queryset

    def queryset_yes_no(self, request, queryset, is_yes):
        raise NotImplementedError



ff = foreign_field