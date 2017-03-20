import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage

class OverwriteStorage(FileSystemStorage):
    """
    Changes the default django pattern and lets it overwrite existing files with the same name
    """
    def get_available_name(self, name):
        print name
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        print name
        return name

def upload_pic(uploaded_file, toFile):
    destination = open(os.path.join(settings.MEDIA_ROOT, toFile), 'wb+')
    for chunk in uploaded_file.chunks():
        destination.write(chunk)
    destination.close()

def read_lines(file, remove_empty=True):
    lines = file.read().splitlines()
    lines = map(lambda s: s.strip(), lines)
    if remove_empty: filter(lambda s: s != '', lines)
    return lines
