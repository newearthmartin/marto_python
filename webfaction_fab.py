import os
from fabric.api import *
import fabfile_settings

@task
def prod():
    env.hosts = [fabfile_settings.PROD_SERVER]
    env.remote_app_dir = os.path.join(fabfile_settings.APP_DIR, fabfile_settings.APP_NAME)
    env.remote_apache_dir = os.path.join(fabfile_settings.APP_DIR, 'apache2')
    env.venv_app = fabfile_settings.VENV_SCRIPT

@task
def pip():
    '''install requirements'''
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    with prefix(env.venv_app):
        run("pip install -r requirements.txt")


@task
def commit():
    message = raw_input("Enter a git commit message:  ")
    local("git add -A && git commit -m \"%s\"" % message)
    local("git push origin master")
    print "Changes have been pushed to remote repository..."

@task
def collectstatic():
    '''collect static files'''
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    with prefix(env.venv_app):
        run("python manage.py collectstatic --noinput")

@task
def restart():
    """Restart apache on the server."""
    require('hosts', provided_by=[prod])
    require('remote_apache_dir', provided_by=[prod])
    run("%s/bin/restart;" % (env.remote_apache_dir))

@task
def deploy():
    '''push, pull, collect static, restart'''
    require('hosts', provided_by=[prod])
    require('remote_app_dir', provided_by=[prod])
    require('venv_app', provided_by=[prod])

    local("git push origin master")

    with prefix(env.venv_app):
        run("git pull")

    collectstatic()
    restart()

@task
def migrate():
    '''execute migrations'''
    require('hosts', provided_by=[prod])
    require('venv_app', provided_by=[prod])
    with prefix(env.venv_app):
        run("python manage.py migrate")
