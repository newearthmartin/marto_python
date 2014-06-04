import os
from optparse import OptionParser

def django_command_line(default_module=None):
    ''' 
    use this method in any command line script that uses django settings
    call this method first thing before importing any other django stuff 
    to configure the settings
    '''
    if not default_module:
        try:
            default_module = os.environ['DJANGO_SETTINGS_MODULE']
        except KeyError:
            pass
    
    usage = "usage: %prog -s SETTINGS | --settings=SETTINGS"
    parser = OptionParser(usage)
    parser.add_option('-s', '--settings', dest='settings', metavar='SETTINGS',
                      help="The Django settings module to use")
    (options, args) = parser.parse_args()
    
    module = options.settings
    if not options.settings:
        if default_module:
            print 'Using already defined DJANGO_SETTINGS_MODULE'
            module = default_module
        else:
            parser.error("You must specify a settings module")
    
    os.environ['DJANGO_SETTINGS_MODULE'] = module
    print 'using settings:', module
