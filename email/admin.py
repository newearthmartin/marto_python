from django import forms
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.widgets import AdminTextInputWidget
from tinymce.widgets import TinyMCE

from marto_python.admin import YesNoFilter
from .management.commands.clean_error_emails import filter_error_emails
from .models import EmailMessage
from .backend import DBEmailBackend


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


class EmailMessageAdmin(ModelAdmin):
    form = EmailMessageAdminForm
    list_display = ['to', 'subject', 'sent', 'send_successful', 'fail_message', 'created_on', 'sent_on']
    list_filter = ['sent', 'send_successful', ErrorsFilter, 'created_on', 'sent_on']
    search_fields = ['from_email', 'to', 'cc', 'bcc', 'subject', 'body', 'fail_message']
    actions = ['send']

    def send(self, _, queryset):
        for email in queryset.all():
            if email.sent and not email.send_successful:
                email.clear_sent()
        DBEmailBackend().send_queryset(queryset)
    send.short_description = "send emails"


admin.site.register(EmailMessage, EmailMessageAdmin)
