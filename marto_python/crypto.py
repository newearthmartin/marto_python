import base64
from Crypto.Cipher import DES
from django.conf import settings


def encrypt_and_encode(string: str) -> str:
    """
    Encrypts and encodes into base 16
    Additional trailing spaces are added to fit len % 8 = 0
    (input should not contain trailing spaces, as they are stripped when decrypting)
    """
    string_bytes = string.encode('utf-8')
    excess = len(string_bytes) % 8
    if excess != 0:
        padding = ' ' * (8 - excess)
        string_bytes += padding.encode('utf-8')
    encrypted = _get_cipher().encrypt(string_bytes)
    return base64.b16encode(encrypted).decode('ascii')


def decode_and_decrypt(string: str) -> str:
    """
    Decodes from base 16 and decrypts.
    """
    encrypted = base64.b16decode(string)
    return _get_cipher().decrypt(encrypted).decode('utf-8').rstrip()


def _get_cipher():
    return DES.new(settings.SECRET_KEY[0:8].encode('utf-8'), DES.MODE_ECB)