import os
from fabric.api import *
from fabfile_settings import fab_settings


def get_app_ssh_path():
    server = fab_settings['PROD_SERVER']
    app_dir = fab_settings['APP_DIR']
    app_django_dir = fab_settings['APP_DJANGO_DIR']
    return f'{server}:{app_dir}/{app_django_dir}'


################ ENVIRONMENT ################


@task
def prod():
    env.environment_name = fab_settings['ENVIRONMENT_NAME']
    env.hosts = [fab_settings['PROD_SERVER']]
    env.webapp_dir = fab_settings['APP_DIR']
    env.restart_script = fab_settings['RESTART_SCRIPT']
    env.venv_app = fab_settings.get('VENV_SCRIPT', f'cd {env.webapp_dir}')
    env.main_branch = fab_settings.get('MAIN_BRANCH', 'master')
    env.port = fab_settings.get('SSH_PORT', 22)


################ GIT ################


@task
def commit():
    message = input('Enter a git commit message: ')
    local(f'git add -A && git commit -m "{message}"')
    print('Changes have been pushed to remote repository...')


@task
def push():
    """
    push and pull
    """
    require('hosts')
    require('venv_app')
    # local('git submodule foreach git push')
    local(f'git push origin {env.main_branch}')
    with prefix(env.venv_app):
        run('git pull')
        run('git submodule update --init --recursive')

################ DEPLOY ################


@task
def pip():
    """
    install requirements
    """
    require('hosts')
    require('venv_app')
    with prefix(env.venv_app):
        run('pip install --upgrade pip')
        run('pip install -r requirements.txt')


@task
def collectstatic():
    """
    collect static files
    """
    require('hosts')
    require('venv_app')
    with prefix(env.venv_app):
        run('python manage.py collectstatic --noinput')


@task
def migrate():
    """
    execute migrations
    """
    require('hosts')
    require('venv_app')
    with prefix(env.venv_app):
        migrate_apps = fab_settings.get('MIGRATE_APPS', '')
        run(f'python manage.py migrate {migrate_apps}')


@task
def requirements():
    """
    install pip requirements
    """
    require('hosts')
    require('venv_app')
    with prefix(env.venv_app):
        run('pip install --upgrade pip')
        run('pip install -r requirements.txt')


@task
def upgrade_pip():
    """
    upgrade pip
    """
    require('hosts')
    require('venv_app')
    with prefix(env.venv_app):
        run('pip install --upgrade pip')


@task
def restart():
    """
    Restart app on the server.
    """
    require('hosts')
    require('restart_script')
    run(env.restart_script)


@task
def deploy():
    """
    push, pull, collect static, restart
    """
    require('hosts')
    require('venv_app')
    push()
    deploy_django()


@task
def deploy_django():
    require('hosts')
    require('venv_app')
    collectstatic()
    migrate()
    restart()


################ DATA ################


@task
def sync_media():
    """
    Download production media files to local computer
    """
    ssh_path = get_app_ssh_path()
    local(f'rsync -avz {ssh_path}/media/ media/')


@task
def db_dump():
    """
    dump entire db on server and retrieve it
    """
    require('hosts')
    require('venv_app')
    dump_data_models = fab_settings['DUMP_DATA_MODELS']

    with prefix(env.venv_app):
        run('mkdir -p data')
        run(f'./manage.py dumpdata {dump_data_models} --indent=2 > data/db.json')
        run('tar cvfz data/db.tgz data/db.json')
        run('rm data/db.json')
    local('mkdir -p data')
    local(f'scp {get_app_ssh_path()}/data/db.tgz data')


@task
def db_load():
    """
    load the whole db on local computer
    """
    local('tar xvfz data/db.tgz')
    local('./manage.py django_clear_tables')
    local('./manage.py loaddata data/db.json')
    local('rm data/db.json')


################ INITIAL DB ################


@task
def initial_dump():
    """
    dump initial data on server and retrieve it
    """
    require('hosts')
    require('venv_app')
    dump_initial_models = fab_settings['DUMP_INITIAL']

    with prefix(env.venv_app):
        run(f'./manage.py dumpdata {dump_initial_models} --indent=2 > data/initial.json')
    local(f'scp {get_app_ssh_path()}/data/initial.json data')


@task
def initial_load():
    """
    load initial data on local computer
    """
    local('./manage.py loaddata data/initial.json')
    if os.path.exists('data/initial_local.json'):
        local('./manage.py loaddata data/initial_local.json')


@task
def reset_local_db():
    """
    resets local db
    """
    username = fab_settings['SUPERUSER_NAME']
    email = fab_settings['SUPERUSER_MAIL']
    local('rm -f db.sqlite3')
    local('./manage.py migrate')
    print('\n\n\nenter admin password:\n\n\n')
    local(f'./manage.py createsuperuser --username {username} --email {email}')
    initial_load()


################ RUN JOBS ################


@task
def hourly():
    """
    run hourly jobs, including submit mails
    """
    require('venv_app')
    with prefix(env.venv_app):
        run('python manage.py runjobs hourly')


@task
def daily():
    """
    run daily jobs
    """
    require('venv_app')
    with prefix(env.venv_app):
        run('python manage.py runjobs daily')


################ CELERY ################


@task
def celery():
    """
    restarts celery
    """
    require('hosts')
    require('venv_app')
    run('monit restart celery')


@task
def monit():
    require('hosts')
    require('venv_app')
    run('monit')
    run('monit status')
