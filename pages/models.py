# FIXME: move to club

from django import forms
from django.db import models
from django.conf import settings
from tinymce.widgets import TinyMCE
from django.db.models.signals import pre_save
from django.contrib import admin


class Pagina(models.Model):
    class Meta:
        verbose_name = 'página'
    url =       models.CharField(max_length=255, unique=True)
    titulo =    models.CharField(max_length=255)
    contenido = models.TextField()
    extra_css = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self): return self.url

    def get_menu(self):
        try:
            return self.menu_set.all()[0]
        except Menu.DoesNotExist:
            return None

    class AdminForm(forms.ModelForm):
        class Meta:
            widgets = {
                'contenido': TinyMCE(attrs={'cols': 100, 'rows': 50}),
            }


class Menu(models.Model):
    class Meta:
        verbose_name = 'menú'
        verbose_name_plural = 'menús'
    titulo =    models.CharField(max_length=255)
    seccion =   models.CharField(max_length=10, choices=settings.MENU_SECTIONS)
    padre =     models.ForeignKey('Menu', null=True, blank=True, related_name='children')
    indice =    models.IntegerField(default=0)
    pagina =    models.ForeignKey('Pagina', null=True, blank=True)
    url =       models.CharField(max_length=255, null=True, blank=True)
    total_url = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        unicode_padre = (unicode(self.padre) + '->') if self.padre else ''
        return unicode_padre + self.titulo

    def get_url(self):
        if self.pagina:
            return self.pagina.url
        else:
            url_padre = self.padre.get_url() if self.padre else ''
            return url_padre + self.url

    def total_index(self):
        index_padre = (self.padre.total_index() + '.') if self.padre else ''
        return index_padre + str(self.indice)

    def ordered_children(self):
        return self.children.order_by('indice')

    class Admin(admin.ModelAdmin):
        list_display = ['__unicode__', 'seccion', 'total_index', 'pagina', 'total_url']
        exclude = ['total_url']

    @staticmethod
    def pre_save(_, **kwargs):
        menu = kwargs['instance']
        menu.total_url = menu.get_url()        
        if menu.pagina:
            menu.url = None
        if menu.url and not menu.url.startswith('http') and not menu.url.startswith('/'):
            menu.url = '/' + menu.url
pre_save.connect(Menu.pre_save, sender=Menu)


class MenuInline(admin.TabularInline):
    model = Menu
    fields = ('titulo', 'indice', 'padre')


class PaginaAdmin(admin.ModelAdmin):
    form = Pagina.AdminForm
    list_display = ['__unicode__', 'url', 'menu_index']
    inlines = [MenuInline]

    @staticmethod
    def menu_index(pagina):
        if pagina.menu_set.count() == 0:
            return 'Sin menu'
        elif pagina.menu_set.count() == 1:
            return pagina.menu_set.all()[0].total_index()
        else:
            return 'más de un menu hacia esta página'
