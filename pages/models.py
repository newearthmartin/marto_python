# coding: utf-8

from django.db import models
from django import forms
from tinymce.widgets import TinyMCE
from django.db.models.signals import pre_save
from django.contrib import admin

class Menu(models.Model):
    class Meta:
        verbose_name = 'menú'
        verbose_name_plural = 'menus'
    titulo = models.CharField(max_length=255)
    padre = models.ForeignKey('Menu', null=True,blank=True, related_name='children')
    indice = models.IntegerField(default=0)
    pagina = models.ForeignKey('Pagina', null=True, blank=True, related_name='menu')
    url = models.CharField(max_length=255, null=True, blank=True)
    totalUrl = models.CharField(max_length=255, null=True, blank=True)
    def __unicode__(self):
        parent = ''
        if self.padre is None:
            parent = ''
        else:
            parent = unicode(self.padre) + '->'
        return parent + self.titulo
    def get_url(self):
        if self.pagina is not None:
            return self.pagina.url
        else:
            if self.padre:
                urlPadre = self.padre.get_url()
            else:
                urlPadre = ''                
            return urlPadre + self.url
    def totalIndex(self):
        if self.padre is None:
            return str(self.indice)
        else:
            return self.padre.totalIndex() + '.' + str(self.indice)
    class Admin(admin.ModelAdmin):
        list_display = ('__unicode__', 'totalIndex', 'pagina', 'totalUrl')
        fields = ['titulo', 'padre', 'indice', 'pagina', 'url']
    @staticmethod
    def pre_save(sender, **kwargs):
        menu = kwargs['instance']
        menu.totalUrl = menu.get_url()        
pre_save.connect(Menu.pre_save, sender=Menu)

class MenuInline(admin.TabularInline):
    model = Menu
    fields = ('titulo', 'indice', 'padre')
    
    
class Pagina(models.Model):
    class Meta:
        verbose_name = 'página'
    url         = models.CharField(max_length=255, unique=True)
    titulo      = models.CharField(max_length=255)
    contenido   = models.TextField()
    extra_css   = models.CharField(max_length=255, blank=True, null=True)
    def __unicode__(self):
        return self.url
    def getMenu(self):
        try:
            return self.menu.all()[0]
        except Menu.DoesNotExist:
            return None
    class AdminForm(forms.ModelForm):
        class Meta:
            widgets = {
                'contenido': TinyMCE(attrs={'cols': 100, 'rows': 50}),
            }
class PaginaAdmin(admin.ModelAdmin):
    form = Pagina.AdminForm
    list_display = ['__unicode__', 'url', 'menuIndex']
    inlines = [MenuInline,]
    def menuIndex(self, pagina):
        if pagina.menu.count() == 0:
            return 'Sin menu'
        elif pagina.menu.count() == 1:
            return pagina.menu.all()[0].totalIndex()
        else:
            return 'más de un menu hacia esta página'
