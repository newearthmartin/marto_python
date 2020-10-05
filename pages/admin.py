from django.contrib import admin
from marto_python.pages.models import Menu, Pagina, PaginaAdmin

admin.site.register(Menu,   Menu.Admin)
admin.site.register(Pagina, PaginaAdmin)
