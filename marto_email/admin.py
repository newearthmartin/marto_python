from django import forms
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.widgets import AdminTextInputWidget
from tinymce.widgets import TinyMCE

from marto_python.admin import FieldsTextInputFilter, YesNoFilter
from .management.commands.clean_error_emails import filter_error_emails
from .models import EmailMessage, MutedAddress
from .backend import DBEmailBackend, default_connection


class EmailMessageAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            'to': AdminTextInputWidget,
            'cc': AdminTextInputWidget,
            'bcc': AdminTextInputWidget,
            'body': TinyMCE(attrs={'cols': 120, 'rows': 50},
                            mce_attrs={
                                'relative_urls': False,
                                'remove_script_host': False,
                            }),
        }


class ErrorsFilter(YesNoFilter):
    title = 'is error'
    parameter_name = 'is_error'

    def queryset_yes_no(self, request, queryset, is_yes):
        return filter_error_emails(queryset, filter_not_exclude=is_yes)


class DestinationFilter(FieldsTextInputFilter):
    title = 'destination'
    parameter_name = 'destination'
    placeholder = 'to, cc or bcc'
    fields = ('to', 'cc', 'bcc')


class FromFilter(FieldsTextInputFilter):
    title = 'from'
    parameter_name = 'from'
    placeholder = 'from'
    fields = ('from_email',)


class SubjectFilter(FieldsTextInputFilter):
    title = 'subject'
    parameter_name = 'subject'
    placeholder = 'subject'
    fields = ('subject',)


class BodyFilter(FieldsTextInputFilter):
    title = 'body'
    parameter_name = 'body'
    placeholder = 'body'
    fields = ('body',)


class EmailMessageAdmin(ModelAdmin):
    form = EmailMessageAdminForm
    list_display = ['to', 'subject', 'sent', 'send_successful', 'fail_message', 'created_on', 'sent_on']
    # text filters instead of search_fields: a search box ORs icontains over every column, body included, which is slow
    list_filter = [DestinationFilter, FromFilter, SubjectFilter, BodyFilter,
                   'sent', 'send_successful', ErrorsFilter, 'created_on', 'sent_on']
    actions = ['send']

    def send(self, _, queryset):
        for email in queryset.all():
            if email.sent and not email.send_successful:
                email.clear_sent()
        default_connection()  # creates the DBEmailBackend instance, with its stack
        DBEmailBackend.instance.send_queryset(queryset)
    send.short_description = "send emails"


admin.site.register(EmailMessage, EmailMessageAdmin)


class MutedAddressAdmin(ModelAdmin):
    list_display = ['address', 'reason', 'created_on']
    search_fields = ['address', 'reason']


admin.site.register(MutedAddress, MutedAddressAdmin)
