from django.contrib import admin
from django.contrib.admin import SimpleListFilter, ModelAdmin
from django.db.models import Model, QuerySet
from .util import is_function


def foreign_field(field_name):
    def accessor(obj):
        val = obj
        for part in field_name.split('__'):
            val = getattr(val, part)
            if val is None:
                return None
        return val if not is_function(val) else val()
    accessor.__name__ = field_name
    return accessor


ff = foreign_field


class YesNoFilter(SimpleListFilter):
    def lookups(self, request, model_admin):
        return [
            ('1', 'yes'),
            ('0', 'no'),
        ]

    def queryset(self, request, queryset) -> QuerySet:
        if self.value():
            queryset = self.queryset_yes_no(request, queryset, self.value() == '1')
        return queryset

    def queryset_yes_no(self, request, queryset, is_yes) -> QuerySet:
        raise NotImplementedError


def register_admin(clazz: type[Model], admin_class: type[ModelAdmin] = None):
    admin.site.register(clazz, admin_class if admin_class else clazz.Admin)
