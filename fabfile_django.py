import os
from fabric.api import *
from fabfile_settings import fab_settings


def get_app_ssh_path():
    return f"{fab_settings['PROD_SERVER']}:{fab_settings['APP_DIR']}/{fab_settings['APP_DJANGO_DIR']}"


################ ENVIRONMENT ################


@task
def prod():
    env.environment_name = fab_settings['ENVIRONMENT_NAME']
    env.hosts = [fab_settings['PROD_SERVER']]
    env.webapp_dir = fab_settings['APP_DIR']
    env.restart_script = fab_settings['RESTART_SCRIPT']
    env.venv_app = fab_settings['VENV_SCRIPT']
    print(f'{env.environment_name} environment')


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
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    # local("git submodule foreach git push")
    local("git push origin master")
    with prefix(env.venv_app):
        run("git pull")
        run("git submodule update --init --recursive")


################ DEPLOY ################


@task
def pip():
    """
    install requirements
    """
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    with prefix(env.venv_app):
        run("pip install -r requirements.txt")


@task
def collectstatic():
    """
    collect static files
    """
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    with prefix(env.venv_app):
        run("python manage.py collectstatic --noinput")


@task
def migrate():
    """
    execute migrations
    """
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    with prefix(env.venv_app):
        migrate_apps = fab_settings['MIGRATE_APPS']
        if not migrate_apps: migrate_apps = ''
        run(f'python manage.py migrate {migrate_apps}')


@task
def requirements():
    """
    install pip requirements
    """
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    with prefix(env.venv_app):
        run("pip install -r requirements.txt")


@task
def upgrade_pip():
    """
    upgrade pip
    """
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    with prefix(env.venv_app):
        run("pip install --upgrade pip")


@task
def restart():
    """
    Restart apache on the server.
    """
    require('hosts', provided_by=[prod])
    require('restart_script', provided_by=[prod])
    with cd(env.webapp_dir):
        run(env.restart_script)


@task
def deploy():
    """
    push, pull, collect static, restart
    """
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    push()
    deploy_django()


@task
def deploy_django():
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    collectstatic()
    migrate()
    restart()


################ DATA ################


@task
def media_sync():
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
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    with prefix(env.venv_app):
        run('mkdir -p data')
        run(f'./manage.py dumpdata {fab_settings["DUMP_DATA_MODELS"]} --indent=4 > data/db.json')
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
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    dump_initial_models = fab_settings["DUMP_INITIAL"]
    with prefix(env.venv_app):
        run(f'./manage.py dumpdata {dump_initial_models} --indent=4 > data/initial.json')
    local(f'scp {get_app_ssh_path()}/data/initial.json data')


@task
def initial_load():
    """
    load initial data on local computer
    """
    local('./manage.py loaddata data/initial.json')


@task
def reset_local_db():
    """
    resets local db
    """
    username = fab_settings['SUPERUSER_NAME']
    email = fab_settings['SUPERUSER_MAIL']
    local('rm db.sqlite3')
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
    require('venv_app', provided_by=[prod])
    with prefix(env.venv_app):
        run("python manage.py runjobs hourly")


################ CELERY ################


@task
def celery():
    """
    restarts celery
    """
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    run('monit restart celery')


@task
def monit():
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    run("monit")
    run("monit status")
