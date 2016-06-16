from django.contrib import admin
from .models import EmailMessage, EmailMessageAdmin

admin.site.register(EmailMessage, EmailMessageAdmin)
