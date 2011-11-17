#!/opt/local/bin/python2.7
'''Check the status of sabnzbd+'''

import json
import urllib2
import urllib
from ConfigParser import SafeConfigParser
from datetime import timedelta, datetime
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import sys
import os


conf_parser = ArgumentParser(add_help=False)
conf_parser.add_argument('-f', '--config-file', dest='config_file', metavar='FILE',
        help='Config file to load')
conf_parser.add_argument('-s', '--section',  dest='section', default='sabnzbd',
        help='Section of Config File to use')
args, remaining_argv = conf_parser.parse_known_args()

parser = ArgumentParser(parents=[conf_parser],
        description=__doc__,
        formatter_class=ArgumentDefaultsHelpFormatter)

if args.config_file:
    config = SafeConfigParser()
    config.read(args.config_file)
    defaults = dict(config.items(args.section))
    parser.set_defaults(**defaults)

parser.add_argument('-a', '--apikey', dest='apikey', help='SABnzbd+ API Key')
parser.add_argument('host', metavar='HOST', help='SABnzbd+ Host')
parser.add_argument('port', metavar='PORT', help='SABnzbd+ Port')
parser.add_argument('-L', '--libdir', dest='libdir', metavar='DIRECTORY', help='timeutils directory')
args = parser.parse_args()
vargs = vars(args)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
if args.libdir:
    sys.path.insert(0, args.libdir)
from timeutils import duration_human

if not args.apikey:
    print 'No API Key'
    exit(1)

params = {
    'mode'  : 'queue',
    'apikey': args.apikey,
    'output': 'json',
    'start' : 0,
    'limit' : 100 }
url = 'http://%s:%s/api?%s' % (args.host, args.port, urllib.urlencode(params))
try:
    data = json.loads(urllib2.urlopen(url).read())['queue']
except urllib2.URLError:
    print 'Not Running'
    exit(0)

if data['status'].lower() in ['idle', 'paused']:
    print data['status']
    exit(0)

hours, minutes, seconds = [int(x) for x in data['timeleft'].split(':')]
delta = timedelta(hours=hours, minutes=minutes, seconds=seconds)

human_left = duration_human(hours * 3600 + minutes * 60 + seconds)

now = datetime.now()
finish = datetime.now() + delta

print '%s %s' % (data['status'],data['noofslots'])
print '%s @ %s' % (human_left, data['eta'])
print '%s Remaining' % data['sizeleft']
print '%sB/s' % data['speed']
