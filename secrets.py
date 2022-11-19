import os
import toml


secrets = None


def read_secrets(base_dir):
    secrets_path = os.path.join(base_dir, 'secrets.toml')
    if os.path.exists(secrets_path):
        with open(secrets_path) as secrets_file:
            global secrets
            secrets = toml.loads(secrets_file.read())


def get_secret(key):
    if secrets and key in secrets:
        return secrets[key]
    else:
        return os.environ.get(key)
