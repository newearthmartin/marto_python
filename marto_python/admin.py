from django.contrib import admin
from django.contrib.admin import SimpleListFilter, ModelAdmin
from django.core.cache import caches
from django.core.paginator import Paginator
from django.db.models import Model, Q, QuerySet
from django.utils.functional import cached_property
from .util import is_function


class NoCountPaginator(Paginator):
    """Paginator that skips the COUNT(*) query — use on admins where the count is too expensive."""

    @cached_property
    def count(self):
        return 9999999999


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


class TextInputFilter(SimpleListFilter):
    """
    A free-text box in the filter sidebar instead of a list of choices - for fields with too
    many values to enumerate (a domain, an email, an id). Subclasses implement filter_value(),
    which only ever sees a non-empty value.

    The template lives in this app (admin/text_input_filter.html), so a project only has to
    have marto_python in INSTALLED_APPS.
    """
    template = 'admin/text_input_filter.html'
    placeholder = ''

    def lookups(self, request, model_admin):
        return ()

    def has_output(self):
        return True

    def filter_value(self, value, queryset) -> QuerySet:
        raise NotImplementedError

    def queryset(self, request, queryset) -> QuerySet:
        value = (self.value() or '').strip()
        return self.filter_value(value, queryset) if value else queryset

    def choices(self, changelist):
        # the box keeps the other active filters, so typing in it narrows rather than replaces
        query_parts = []
        for key, value in changelist.params.items():
            if key in {self.parameter_name, 'p'}:
                continue
            if isinstance(value, (list, tuple)):
                query_parts.extend((key, item) for item in value)
            else:
                query_parts.append((key, value))
        yield {
            'query_parts': query_parts,
            'value': self.value() or '',
            'clear_query_string': changelist.get_query_string(remove=[self.parameter_name]),
        }


class FieldsTextInputFilter(TextInputFilter):
    """Matches what was typed against any of `fields` (icontains)."""
    fields = ()
    distinct = False

    def filter_value(self, value, queryset):
        q = Q()
        for field in self.fields:
            q |= Q(**{f'{field}__icontains': value})
        queryset = queryset.filter(q)
        return queryset.distinct() if self.distinct else queryset


def text_input_filter_class(name, base=FieldsTextInputFilter, **attrs):
    """A filter class per admin, since a SimpleListFilter carries its fields on the class."""
    return type(name, (base,), attrs)


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
    def __init__(self, request, params, model, model_admin, ttl=24 * 60 * 60):
        self.model = model
        self.ttl = ttl
        self.null_key, self.null_value = self.null_key_value()
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        cache = caches['default']
        cache_key = f'field_list_filter.{self.model.__module__}.{self.model.__name__}.{self.field_name}'
        values = cache.get(cache_key)
        if values is None:
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
