import os
import toml


secrets = None


def read_secrets(base_dir=None, secrets_file=None):
    if not secrets_file:
        secrets_file = 'secrets.toml'
    secrets_path = os.path.join(base_dir, secrets_file) if base_dir else secrets_file
    if os.path.exists(secrets_path):
        with open(secrets_path) as secrets_file:
            global secrets
            secrets = toml.loads(secrets_file.read())


def get_secret(key, default=None):
    if secrets and key in secrets:
        return secrets[key]
    else:
        return os.environ.get(key, default=default)
