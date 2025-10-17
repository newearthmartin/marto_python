import os
from fabric import Connection
from invoke import task

from fabric import Config

__prod = None


def get_prod(c):
    global __prod
    if not __prod:
        config = Config(overrides={"run": {"echo": True}})
        host = c.default.host
        user = getattr(c.default, "user", None)
        port = getattr(c.default, "port", None)
        __prod = Connection(host=host, user=user, port=port, config=config)
    return __prod


def prod_server(c):
    host = c.default.host
    user = getattr(c.default, "user", None)
    return f'{user}@{host}' if user else host


def app_ssh_path(c):
    app_dir = c.settings.app_dir
    app_django_dir = getattr(c.settings, 'app_django_dir', None)
    path = f'{app_dir}/{app_django_dir}' if app_django_dir else app_dir
    return f'{prod_server(c)}:{path}'


def app_prefix(c, conn):
    prefix = getattr(c.settings, 'venv_script', None) or f'cd {c.settings.app_dir}'
    return conn.prefix(prefix)


def scp_cmd(c):
    cmd = 'scp'
    if port := getattr(c.default, 'port', None):
        cmd += f' -P {port}'
    return cmd


def rsync_cmd(c):
    cmd = 'rsync'
    if port := getattr(c.default, 'port', None):
        cmd += f' -e "ssh -p {port}"'
    return cmd


@task
def hello(c):
    conn = get_prod(c)
    conn.run('echo hello: `pwd` - `uname -a`')


# ############### GIT ################


@task
def commit(c):
    """
    Commit changes
    """
    conn = get_prod(c)
    message = input('Enter a git commit message: ')
    conn.local(f'git add -A && git commit -m "{message}"')
    print('Changes have been pushed to remote repository...')


@task
def push(c):
    """
    Push and pull
    """
    conn = get_prod(c)

    main_branch = getattr(c.settings, 'main_branch', 'main')
    conn.local(f'git push origin {main_branch}')
    with app_prefix(c, conn):
        conn.run('git pull')
        conn.run('git submodule update --init --recursive')


# ############### DEPLOY ################


@task
def requirements(c):
    """
    Installs requirements.
    Defaults to uv. Set uv_not_pip as false to fall back to pip.
    """
    if getattr(c.settings, 'uv_not_pip', True):
        cmds = ['uv sync --no-dev']
    else:
        cmds = ['pip install --upgrade pip', 'pip install -r requirements.txt']
    conn = get_prod(c)
    with app_prefix(c, conn):
        for cmd in cmds:
            conn.run(cmd)


@task
def uvlocal(c):
    get_prod(c).local('uv sync --no-group server')


@task
def collect_static(c):
    """
    Collect static files
    """
    conn = get_prod(c)
    with app_prefix(c, conn):
        conn.run('./manage.py collectstatic --noinput')


@task
def migrate(c):
    """
    Execute migrations
    """
    conn = get_prod(c)
    with app_prefix(c, conn):
        migrate_apps = c.settings.get('migrate_apps', None)
        conn.run('./manage.py migrate' + (f' {migrate_apps}' if migrate_apps else ''))


@task
def restart(c):
    """
    Restart app on the server
    """
    conn = get_prod(c)
    conn.run(c.settings.restart_script)


@task
def deploy(c):
    """
    Push, pull, collect static, restart
    """
    push(c)
    requirements(c)
    collect_static(c)
    migrate(c)
    restart(c)


# ############### DATA ################


@task
def sync_media(c):
    """
    Download production media files to local computer
    """
    conn = get_prod(c)
    rsync = rsync_cmd(c)
    conn.local(f'{rsync} -avz {app_ssh_path(c)}/media/ media/')


@task
def db_dump(c):
    """
    Dump entire db on server and retrieve it
    """
    models = getattr(c.settings, 'dump_data_models', None)
    conn = get_prod(c)
    with app_prefix(c, conn):
        conn.run('mkdir -p data', hide=True)
        conn.run(f'./manage.py dumpdata {models or ''} --indent=2 > data/db.json')
        conn.run('tar cvfz data/db.tgz data/db.json')
        conn.run('rm data/db.json', hide=True)
    conn.local('mkdir -p data', hide=True)
    scp = scp_cmd(c)
    conn.local(f'{scp} {app_ssh_path(c)}/data/db.tgz data')


@task
def db_load(c):
    """
    Load the dumped db on local computer
    """
    conn = get_prod(c)
    conn.local('tar xvfz data/db.tgz')
    conn.local('./manage.py django_clear_tables')
    conn.local('./manage.py loaddata data/db.json')
    conn.local('rm data/db.json')


# ############### INITIAL DB ################


@task
def initial_dump(c):
    """
    Dump initial data on server and retrieve it
    """
    conn = get_prod(c)
    with app_prefix(c, conn):
        conn.run('mkdir -p data', hide=True)
        conn.run(f'./manage.py dumpdata {c.settings.dump_initial} --indent=2 > data/initial.json')

    scp = scp_cmd(c)
    conn.local(f'{scp} {app_ssh_path(c)}/data/initial.json data')


@task
def initial_load(c):
    """
    Load initial data on local computer
    """
    conn = get_prod(c)
    conn.local('./manage.py loaddata data/initial.json')
    if os.path.exists('data/initial_local.json'):
        conn.local('./manage.py loaddata data/initial_local.json')


@task
def reset_local_db(c):
    """
    Resets local db
    """
    conn = get_prod(c)
    conn.local('rm -f db.sqlite3')
    conn.local('./manage.py migrate')
    createsuperuser(c)
    initial_load(c)


@task
def createsuperuser(c):
    conn = get_prod(c)
    user = c.settings.superuser_user
    email = c.settings.superuser_mail
    print('\n\n\nEnter admin password:\n\n\n')
    conn.local(f'./manage.py createsuperuser --username {user} --email {email}', pty=True)


# ############### RUN JOBS ################


def __run_jobs(c, job_type):
    conn = get_prod(c)
    with app_prefix(c, conn):
        conn.run(f'./manage.py runjobs {job_type}')


@task
def hourly(c):
    """
    Run hourly jobs
    """
    __run_jobs(c, 'hourly')


@task
def daily(c):
    """
    Run daily jobs
    """
    __run_jobs(c, 'daily')


# ############### CELERY ################


@task
def celery(c):
    """
    Restarts celery
    """
    conn = get_prod(c)
    conn.run(c.settings.restart_celery_script)


@task
def monit(c):
    """
    Monit status
    """
    conn = get_prod(c)
    if monitrc := getattr(c.settings, 'monitrc', None):
        conn.run(f'chmod 700 {monitrc}')
    conn.run('monit')
    conn.run('monit reload')
    conn.run('monit status')
