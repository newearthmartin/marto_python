import os
from fabric import Connection
from invoke import task

from fabric import Config

__prod = None
def get_prod(c):
    global __prod
    if not __prod:
        config = Config(overrides={"run": {"echo": True}})
        __prod = Connection(host=c.default.host, user=c.default.user, config=config)
    return __prod


def app_ssh_path(c):
    return f'{c.settings.prod_server}:{c.settings.app_dir}/{c.settings.app_django_dir}'


################ GIT ################


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
    conn.local(f'git push origin {c.settings.main_branch}')
    with conn.prefix(c.settings.venv_script):
        conn.run('git pull')
        conn.run('git submodule update --init --recursive')



################ DEPLOY ################


@task
def pip(c):
    """
    Install requirements
    """
    pip = getattr(c.settings, 'pip', 'pip')
    print(f'Using pip: {pip}')
    conn = get_prod(c)
    with conn.prefix(c.settings.venv_script):
        conn.run(f'{pip} install --upgrade pip')
        conn.run(f'{pip} install -r requirements.txt')


@task
def collect_static(c):
    """
    Collect static files
    """
    conn = get_prod(c)
    with conn.prefix(c.settings.venv_script):
        conn.run('python manage.py collectstatic --noinput')


@task
def migrate(c):
    """
    Execute migrations
    """
    conn = get_prod(c)
    with conn.prefix(c.settings.venv_script):
        migrate_apps = c.settings.get('migrate_apps', None)
        conn.run('python manage.py migrate' + (f' {migrate_apps}' if migrate_apps else ''))


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
    collect_static(c)
    migrate(c)
    restart(c)


################ DATA ################


@task
def sync_media(c):
    """
    Download production media files to local computer
    """
    conn = get_prod(c)
    conn.local(f'rsync -avz {app_ssh_path(c)}/media/ media/')


@task
def db_dump(c):
    """
    Dump entire db on server and retrieve it
    """
    conn = get_prod(c)
    with conn.prefix(c.settings.venv_script):
        conn.run('mkdir -p data', hide=True)
        conn.run(f'./manage.py dumpdata {c.settings.dump_data_models} --indent=2 > data/db.json')
        conn.run('tar cvfz data/db.tgz data/db.json')
        conn.run('rm data/db.json', hide=True)
    conn.local('mkdir -p data', hide=True)
    conn.local(f'scp {app_ssh_path(c)}/data/db.tgz data')


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




################ INITIAL DB ################


@task
def initial_dump(c):
    """
    Dump initial data on server and retrieve it
    """
    conn = get_prod(c)
    with conn.prefix(c.settings.venv_script):
        conn.run(f'./manage.py dumpdata {c.settings.dump_initial} --indent=2 > data/initial.json')
    conn.local(f'scp {app_ssh_path(c)}/data/initial.json data')


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
    resets local db
    """
    conn = get_prod(c)
    conn.local('rm -f db.sqlite3')
    conn.local('./manage.py migrate')
    print('\n\n\nEnter admin password:\n\n\n')
    conn.local(f'./manage.py createsuperuser --username {c.settings.superuser_user} --email {c.settings.superuser_mail}', pty=True)
    initial_load(c)



################ RUN JOBS ################


def __run_jobs(c, job_type):
    conn = get_prod(c)
    with conn.prefix(c.settings.venv_script):
        conn.run(f'python manage.py runjobs {job_type}')

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


################ CELERY ################


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
    conn.run('monit')
    conn.run('monit status')
