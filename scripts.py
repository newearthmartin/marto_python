import os
from optparse import OptionParser

def djangoCommandline(defaultModule=None):
    if not defaultModule:
        try:
            defaultModule = os.environ['DJANGO_SETTINGS_MODULE']
        except KeyError:
            pass
    
    usage = "usage: %prog -s SETTINGS | --settings=SETTINGS"
    parser = OptionParser(usage)
    parser.add_option('-s', '--settings', dest='settings', metavar='SETTINGS',
                      help="The Django settings module to use")
    (options, args) = parser.parse_args()
    
    module = options.settings
    if not options.settings:
        if defaultModule:
            print 'Using already defined DJANGO_SETTINGS_MODULE'
            module = defaultModule
        else:
            parser.error("You must specify a settings module")
    
    os.environ['DJANGO_SETTINGS_MODULE'] = module
    print 'using settings:', module
