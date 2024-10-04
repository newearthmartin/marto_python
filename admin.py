from django.contrib import admin
from django.contrib.admin import SimpleListFilter, ModelAdmin
from django.core.cache import caches
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


# noinspection PyMethodMayBeStatic
class CachedFieldListFilter(SimpleListFilter):
    def __init__(self, request, params, model, model_admin, field_name, ttl=24 * 60 * 60):
        self.field_name = field_name
        self.model = model
        self.ttl = ttl
        self.null_key, self.null_value = self.null_key_value()
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        cache = caches['default']
        cache_key = f'filter.{self.model}.{self.field_name}'
        values = cache.get(cache_key)
        if values is None or True:
            values = self.model.objects.values_list(self.field_name).distinct().order_by(self.field_name).all()
            values = [v[0] for v in values]
            has_none = None in values
            values = [(self.value_to_key(v), str(v)) for v in values if v is not None]
            if has_none:
                values.append((self.null_key, self.null_value))
            cache.set(cache_key, values, self.ttl)
        return values

    def null_key_value(self): return 'null', '-'
    def value_to_key(self, v): return str(v)
    def key_to_filter_value(self, v): return v

    def queryset(self, request, queryset):
        if self.value():
            field_value = self.key_to_filter_value(self.value()) if self.value() != self.null_key else None
            params = {self.field_name: field_value}
            queryset = queryset.filter(**params)
        return queryset



def register_admin(clazz: type[Model], admin_class: type[ModelAdmin] = None):
    admin.site.register(clazz, admin_class if admin_class else clazz.Admin)
