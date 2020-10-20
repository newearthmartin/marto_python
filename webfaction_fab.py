import os
from fabric.api import *
from fabfile_settings import fab_settings


def get_app_ssh_path():
    return f"{fab_settings['PROD_SERVER']}:{fab_settings['APP_DIR']}/{fab_settings['DJANGO_APP_DIR']}"


################ ENVIRONMENT ################


@task
def prod():
    print('PRODUCTION environment')
    env.hosts = [fab_settings['PROD_SERVER']]
    env.webapp_dir = fab_settings['APP_DIR']
    env.remote_app_dir = os.path.join(env.webapp_dir, fab_settings['DJANGO_DIR'])
    env.restart_script = fab_settings['RESTART_SCRIPT']
    env.venv_app = fab_settings['VENV_SCRIPT']


@task
def test():
    print('TEST environment')
    prod()
    env.venv_app = fab_settings['VENV_SCRIPT_TEST']


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
    require('remote_app_dir', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    push()
    deploy_django()


@task
def deploy_django():
    require('hosts', provided_by=[prod])
    require('remote_app_dir', provided_by=[prod])
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
    local(f'rsync -avz {get_app_ssh_path()}/media/ media/')


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
