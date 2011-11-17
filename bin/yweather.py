#!/opt/local/bin/python2.7
# -*- Encoding: utf-8 -*-

# Get and print Yahoo! Weather information
# See http://developer.yahoo.com/weather/ for information

from xml.dom.minidom import parse
import urllib
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from ConfigParser import SafeConfigParser

data = ( 
    'title',
    'temp',
    'text',
    'date',
    'code',
    'today-high',
    'today-low',
    'today-text',
    'today-date',
    'today-day',
    'today-code',
    'tomorrow-high',
    'tomorrow-low',
    'tomorrow-text',
    'tomorrow-date',
    'tomorrow-day',
    'tomorrow-code',
    'wind-chill',
    'wind-direction'
    'wind-speed',
    'humidity',
    'visibility',
    'pressure',
    'rising',
    'sunrise',
    'sunset'
)

code = (
    'Tornado',
    'Tropical Storm',
    'Hurricane',
    'Severe Thunderstorms',
    'Thunderstorms',
    'Mixed Rain and Snow',
    'Mixed Rain and Sleet',
    'Mixed Snow and Sleet',
    'Freezing Drizzle',
    'Drizzle',
    'Freezing Rain',
    'Showers',
    'Showers',
    'Snow Flurries',
    'Light Snow Showers',
    'Blowing Snow',
    'Snow',
    'Hail',
    'Sleet',
    'Dust',
    'Foggy',
    'Haze',
    'Smoky',
    'Blustery',
    'Windy',
    'Cold',
    'Cloudy',
    'Mostly Cloudy (Night)',
    'Mostly Cloudy (Day)',
    'Partly Cloudy (Night)',
    'Partly Cloudy (Day)',
    'Clear (Night)',
    'Sunny',
    'Fair (Night)',
    'Fair (Day)',
    'Mixed Rain and Hail',
    'Hot',
    'Isolated Thunderstorms',
    'Scattered Thunderstorms',
    'Scattered Thunderstorms',
    'Scattered Showers',
    'Heavy Snow',
    'Scattered Snow Showers',
    'Heavy Snow',
    'Partly Cloudy',
    'Thundershowers',
    'Snow Showers',
    'Isolated Thundershowers',
    'Not Available')


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

parser.add_argument("-w", "--woeid", dest="woeid", default="12792014", help="WOEID")
parser.add_argument("-u", "--units", dest="units", default="f", choices=['f', 'c'], help="Degree Units")
parser.add_argument("-t", "--template", dest="template", help="Output Format template")
parser.add_argument("-j", "--join", dest="join", default="\n", help="Join Character")
(args, remaining_argv) = parser.parse_known_args()

uri = 'http://weather.yahooapis.com/forecastrss?%s'
params = urllib.urlencode({'w':args.woeid, 'u':args.units})
try:
    dom = parse(urllib.urlopen(uri % params))
except IOError as (errno, strerror):
    print "I/O error({0}): {1}".format(errno, strerror)
    exit(1)

xmlns = 'http://xml.weather.yahoo.com/ns/rss/1.0'
full_title = dom.getElementsByTagName('title')[0].firstChild.data
title = full_title.replace("Yahoo! Weather - ", '')

condition = dom.getElementsByTagNameNS(xmlns, 'condition')[0]
wind = dom.getElementsByTagNameNS(xmlns, 'wind')[0]
atmosphere = dom.getElementsByTagNameNS(xmlns, 'atmosphere')[0]
astronomy = dom.getElementsByTagNameNS(xmlns, 'astronomy')[0]
(today, tomorrow) = tuple(dom.getElementsByTagNameNS(xmlns, 'forecast'))

units = dom.getElementsByTagNameNS(xmlns, 'units')[0]
dc = unichr(176) # Degree symbol
tu = units.getAttribute('temperature')
su = units.getAttribute('speed')
du = units.getAttribute('distance')
pu = units.getAttribute('pressure')

rising_words = ('Steady', 'Rising', 'Falling')

def utf8(s):
    return s.encode('utf-8')

results = { 
    'title'         : title,
    'temp'          : utf8(condition.getAttribute('temp') + dc),
    'text'          : condition.getAttribute('text'),
    'date'          : condition.getAttribute('date'),
    'code'          : code[int(condition.getAttribute('code'))],

    'today-high'    : utf8(today.getAttribute('high') + dc),
    'today-low'     : utf8(today.getAttribute('low') + dc),
    'today-text'    : today.getAttribute('text'),
    'today-date'    : today.getAttribute('date'),
    'today-day'     : today.getAttribute('day'),
    'today-code'    : code[int(today.getAttribute('code'))],

    'tomorrow-high' : utf8(tomorrow.getAttribute('high') + dc),
    'tomorrow-low'  : utf8(tomorrow.getAttribute('low') + dc),
    'tomorrow-text' : tomorrow.getAttribute('text'),
    'tomorrow-date' : tomorrow.getAttribute('date'),
    'tomorrow-day'  : tomorrow.getAttribute('day'),
    'tomorrow-code' : code[int(tomorrow.getAttribute('code'))],

    'wind-chill'    : wind.getAttribute('chill') + dc,
    'wind-direction': wind.getAttribute('direction'),
    'wind-speed'    : wind.getAttribute('speed') + " " + su,

    'humidity'      : atmosphere.getAttribute('humidity') + '%',
    'visibility'    : atmosphere.getAttribute('visibility') + " " + du,
    'pressure'      : atmosphere.getAttribute('pressure') + " " + pu,
    'rising'        : rising_words[int(atmosphere.getAttribute('rising'))],

    'sunrise'       : astronomy.getAttribute('sunrise'),
    'sunset'        : astronomy.getAttribute('sunset')
}

if args.template:
    print args.template.format(**results)
else:
    print args.join.join(results[x] for x in remaining_argv)

