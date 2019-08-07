import os
from fabric.api import *
from fabfile_settings import fab_settings


def get_app_ssh_path():
    return '%s:%s/%s' % (fab_settings['PROD_SERVER'], fab_settings['APP_DIR'], fab_settings['APP_NAME'])


################ ENVIRONMENT ################


@task
def prod():
    print 'PRODUCTION environment'
    env.hosts = [fab_settings['PROD_SERVER']]
    env.remote_app_dir = os.path.join(fab_settings['APP_DIR'], fab_settings['APP_NAME'])
    env.remote_apache_dir = os.path.join(fab_settings['APP_DIR'], 'apache2')
    env.venv_app = fab_settings['VENV_SCRIPT']


@task
def test():
    print 'TEST environment'
    env.hosts = [fab_settings['PROD_SERVER']]
    env.remote_app_dir = os.path.join(fab_settings['APP_DIR_TEST'], fab_settings['APP_NAME'])
    env.remote_apache_dir = os.path.join(fab_settings['APP_DIR_TEST'], 'apache2')
    env.venv_app = fab_settings['VENV_SCRIPT_TEST']


################ GIT ################


@task
def commit():
    message = raw_input("Enter a git commit message:  ")
    local("git add -A && git commit -m \"%s\"" % message)
    print "Changes have been pushed to remote repository..."


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
        run("python manage.py migrate %s" % migrate_apps)


@task
def restart():
    """
    Restart apache on the server.
    """
    require('hosts', provided_by=[prod])
    require('remote_apache_dir', provided_by=[prod])
    run("%s/bin/restart;" % env.remote_apache_dir)


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
    local('rsync -avz %s/media/ media/' % get_app_ssh_path())


@task
def db_dump():
    """
    dump entire db on server and retrieve it
    """
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    with prefix(env.venv_app):
        run("mkdir -p data")
        run("./manage.py dumpdata %s --indent=4 > data/db.json" % fab_settings['DUMP_DATA_MODELS'])
        run("tar cvfz data/db.tgz data/db.json")
        run("rm data/db.json")
    local("mkdir -p data")
    local('scp %s/data/db.tgz data' % get_app_ssh_path())


@task
def db_load():
    """
    load the whole db on local computer
    """
    local('tar xvfz data/db.tgz')
    local('./manage.py loaddata data/db.json')
    local('rm data/db.json')
