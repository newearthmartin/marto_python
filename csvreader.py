# -*- coding: utf-8 -*-

import csv, codecs, hashlib
from django.contrib.auth.models import User
from cms.models import PerfilUsuario, Suscripcion, TipoDestacado


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)
        self.encoding = encoding

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode('utf-8')

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="latin-1", delimiter=';', **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, delimiter=delimiter, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self




class UserReader:

    def __init__(self,filename):
        self.filename = filename
        self.reader = UnicodeReader(open(filename))
        PerfilUsuario.objects.filter(fromOldDB=True).exclude(user__is_staff=True).delete()

    def read(self):

        i = 0
        for line in self.reader:
            if i == 0 :
                """
                it is the header. skip it.
                """
                i = 1
                continue
            
            if i == 50 :
                break

            codigo = line[0]
            apellido = line[1]
            nombres = line[2]
            _estado = line[3]
            mail = line[4]
            disco_del_mes = 'mes' in line[5].lower()
            folklore = 'america' in line[5].lower()
            self.save_model(codigo=codigo,apellido=apellido,nombres=nombres,email=mail,disco_del_mes=disco_del_mes,folklore=folklore)



    def save_model(self,codigo=0,apellido='',nombres='',email='',disco_del_mes=False,folklore=False):
        username = email.split("@")[0]
        if User.objects.filter(username=username).count():
            username = username + str(codigo)

        usuario = User.objects.create_user(username=username,email=email,password=hashlib.md5(username).hexdigest()[:8])
        usuario.first_name=nombres
        usuario.last_name=apellido
        usuario.save()

        pfu = PerfilUsuario()
        pfu.numeroSocio = codigo
        pfu.fromOldDB = True
        pfu.user = usuario

        if disco_del_mes:
            tipo_suscripcion = TipoDestacado.objects.get(tipo__icontains='mes')
            pfu.socio = True
            Suscripcion(user=usuario,tipo=tipo_suscripcion).save()
        if folklore:
            tipo_suscripcion = TipoDestacado.objects.get(tipo__icontains='mundo')
            Suscripcion(user=usuario,tipo=tipo_suscripcion).save()
            pfu.socio = True

        pfu.save()
