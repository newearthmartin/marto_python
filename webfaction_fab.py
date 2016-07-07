import os
from fabric.api import *
import fabfile_settings

@task
def prod():
    print 'PRODUCTION environment'
    env.hosts = [fabfile_settings.PROD_SERVER]
    env.remote_app_dir = os.path.join(fabfile_settings.APP_DIR, fabfile_settings.APP_NAME)
    env.remote_apache_dir = os.path.join(fabfile_settings.APP_DIR, 'apache2')
    env.venv_app = fabfile_settings.VENV_SCRIPT

@task
def test():
    print 'TEST environment'
    env.hosts = [fabfile_settings.PROD_SERVER]
    env.remote_app_dir = os.path.join(fabfile_settings.APP_DIR_TEST, fabfile_settings.APP_NAME)
    env.remote_apache_dir = os.path.join(fabfile_settings.APP_DIR_TEST, 'apache2')
    env.venv_app = fabfile_settings.VENV_SCRIPT_TEST


@task
def pip():
    '''install requirements'''
    require('hosts')
    require('venv_app')
    with prefix(env.venv_app):
        run("pip install -r requirements.txt")

@task
def commit():
    message = raw_input("Enter a git commit message:  ")
    local("git add -A && git commit -m \"%s\"" % message)
    print "Changes have been pushed to remote repository..."

@task
def push():
    '''push and pull'''
    require('hosts')
    require('venv_app')
    local("git push origin master")
    with prefix(env.venv_app):
        run("git pull")
        run("git submodule init")
        run("git submodule update")

@task
def collectstatic():
    '''collect static files'''
    require('hosts')
    require('venv_app')
    with prefix(env.venv_app):
        run("python manage.py collectstatic --noinput")

@task
def migrate():
    '''execute migrations'''
    require('hosts')
    require('venv_app')
    with prefix(env.venv_app):
        run("python manage.py migrate")

@task
def restart():
    """Restart apache on the server."""
    require('hosts')
    require('remote_apache_dir')
    run("%s/bin/restart;" % (env.remote_apache_dir))

@task
def deploy():
    '''push, pull, collect static, migrate, restart'''
    require('hosts')
    require('remote_app_dir')
    require('venv_app')
    push()
    collectstatic()
    migrate()
    restart()
