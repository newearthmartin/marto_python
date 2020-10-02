import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):

    def get_available_name(self, name, max_length=None):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        This file storage solves overwrite on upload problem.
        Found at http://djangosnippets.org/snippets/976/
        """
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name


def upload_pic(uploaded_file, to_file):
    destination = open(os.path.join(settings.MEDIA_ROOT, to_file), 'wb')
    for chunk in uploaded_file.chunks():
        destination.write(chunk)
    destination.close()


def read_lines(f, remove_empty=False):
    lines = f.read().splitlines()
    lines = [line.strip() for line in lines]
    if remove_empty: lines = [s for s in lines if s]
    return lines
