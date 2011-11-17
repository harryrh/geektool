#!/opt/local/bin/python2.7
'''Get 7 day forecast icons from Weather Underground and 
generate a horizontal and/or montage of the icons'''

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from ConfigParser import SafeConfigParser
import urllib
import os
import sys
from cStringIO import StringIO

from BeautifulSoup import BeautifulStoneSoup
from PIL import Image

conf_parser = ArgumentParser(add_help=False)
conf_parser.add_argument('-f', '--config-file', dest='config_file', metavar='FILE',
        help='Config file to load')
conf_parser.add_argument('-s', '--section',  dest='section', default='wunderground',
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

parser.add_argument('-L', '--libdir', dest='libdir', metavar='DIRECTORY',
        default='/usr/local/geektool/lib', help='imageutils directory')
parser.add_argument('-V', '--vertical', dest='vertical', metavar='FILE', help='Vertical Montage File Name')
parser.add_argument('-H', '--horizontal', dest='horizontal', metavar='FILE', help='Horizontal Montage File Name')
parser.add_argument('search')
args = parser.parse_args()
vargs = vars(args)

sys.path.append(args.libdir)
from imageutils import horizontal_montage, vertical_montage

uri = 'http://chrome.wunderground.com/auto/chrome/geo/wx/index.html?%s'
url = uri % urllib.urlencode({'query': args.search})

soup = BeautifulStoneSoup(urllib.urlopen(url))

images = []
for i, d in enumerate(soup.findAll('div', attrs={'class': ['icon']})):
    im = Image.open(StringIO(urllib.urlopen(d.img['src']).read()))
    images.append(im)
    
if args.vertical:
    vm = vertical_montage(images, halign='center')
    vm.save(args.vertical)

if args.horizontal:
    hm = horizontal_montage(images, valign='top')
    hm.save(args.horizontal)
