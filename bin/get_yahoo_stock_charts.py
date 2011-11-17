#!/opt/local/bin/python2.7
'''Grab stock charts from yahoo.  Save the images individually and as montages'''

import sys
import urllib
import shlex
from ConfigParser import SafeConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import threading
import os

from PIL import Image

conf_parser = ArgumentParser(add_help=False)
conf_parser.add_argument('-f', '--config-file', dest='config_file', metavar='FILE',
        help='Config file to load')
conf_parser.add_argument('-s', '--section',  dest='section', default='stocks',
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

parser.add_argument('-z', '--size', dest='size',
        choices=['s', 'm', 'l'], default='l', help='Image size')
parser.add_argument('-S', '--symbol', dest='symbols',
        help='Specify stock symbols -- space separated list')
parser.add_argument('-o', '--output-dir',
        dest='output', help='Output Directory')
parser.add_argument('-V', '--vertical',
        dest='vertical', help='Vertical montage file')
parser.add_argument('-H', '--horizonal',
        dest='horizontal', help='Horizonal montage file')
parser.add_argument('-L', '--libdir', dest='libdir', metavar='DIR', help='imageutils directory')
args = parser.parse_args()

symbols = shlex.split(args.symbols)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
if args.libdir:
    sys.path.insert(0, args.libdir)
from imageutils import horizontal_montage, vertical_montage

# http://chart.finance.yahoo.com/t?s=AAPL&lang=en-US&region=US&width=300&height=180
# uri = 'http://chart.finance.yahoo.com/t?%s'
# http://chart.finance.yahoo.com/z?s=AAPL&t=1d&z=l&p=b&lang=en-US&region=US
uri = 'http://chart.finance.yahoo.com/z?%s'

threads = []

try:
    os.makedirs(args.output)
except:
    pass

# Go get the images
for symbol in symbols:
    params = urllib.urlencode({'s':symbol, 'lang':'en-US', 'region':'US', 't':'1d', 'p':'b', 'z':args.size});
    url = uri % params
    dest = "%s/%s.png" % (args.output, symbol)
    t = threading.Thread(target=urllib.urlretrieve, args=(url, dest))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

images = []

# Generate the montage images
for symbol in symbols:
    file = "%s/%s.png" % (args.output, symbol)
    im = Image.open(file)
    images.append(im)

if args.vertical:
    vm = vertical_montage(images, halign='center')
    vm.save(args.vertical)

if args.horizontal:
    hm = horizontal_montage(images, valign='top')
    hm.save(args.horizontal)
