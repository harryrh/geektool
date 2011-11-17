#!/opt/local/bin/python2.7
'''Get 7 day forecast icons from Weather Underground and 
generate a horizontal and/or montage of the icons'''

from ConfigParser import SafeConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from cStringIO import StringIO
import os
import sys
import urllib

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

parser.add_argument('-V', '--vertical', dest='vertical', metavar='FILE', help='Vertical Montage File Name')
parser.add_argument('-H', '--horizontal', dest='horizontal', metavar='FILE', help='Horizontal Montage File Name')
parser.add_argument('-L', '--libdir', dest='libdir', metavar='DIRECTORY', help='imageutils directory')
parser.add_argument('search')
args = parser.parse_args()
vargs = vars(args)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
if args.libdir:
    sys.path.insert(0, args.libdir)
from imageutils import horizontal_montage, vertical_montage

uri = 'http://chrome.wunderground.com/auto/chrome/geo/wx/index.html?%s'
url = uri % urllib.urlencode({'query': args.search})

soup = BeautifulStoneSoup(urllib.urlopen(url))

images = []
for i, d in enumerate(soup.findAll('div', 'icon')):
    im = Image.open(StringIO(urllib.urlopen(d.img['src']).read()))
    images.append(im)
    
if args.vertical:
    vm = vertical_montage(images, halign='center')
    vm.save(args.vertical)

if args.horizontal:
    hm = horizontal_montage(images, valign='top')
    hm.save(args.horizontal)
