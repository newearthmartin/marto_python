from django import forms
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.widgets import AdminTextInputWidget
from tinymce.widgets import TinyMCE

from .models import EmailMessage
from .backend import DBEmailBackend


class EmailMessageAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            'to': AdminTextInputWidget,
            'cc': AdminTextInputWidget,
            'bcc': AdminTextInputWidget,
            'body': TinyMCE(attrs={'cols': 120, 'rows': 50}),
        }


class EmailMessageAdmin(ModelAdmin):
    form = EmailMessageAdminForm
    list_display = ['to', 'subject', 'sent', 'send_successful', 'fail_message', 'created_on', 'sent_on']
    list_filter = ['sent', 'send_successful', 'created_on', 'sent_on']
    search_fields = ['from_email', 'to', 'cc', 'bcc', 'subject', 'body', 'fail_message']
    actions = ['send']

    def send(self, _, queryset):
        for email in queryset.all():
            if email.sent and not email.send_successful:
                email.clear_sent()
        DBEmailBackend().send_queryset(queryset)
    send.short_description = "send emails"


admin.site.register(EmailMessage, EmailMessageAdmin)
