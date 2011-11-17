#!/opt/local/bin/python2.7

# Get and Yahoo! Weather information -- save images
# See http://developer.yahoo.com/weather/ for information

from xml.dom.minidom import parse, parseString
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup, SoupStrainer
import sys
import string
import urllib
import os
import re

parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        epilog='The file is saved as IMAGE_DIR/IMAGE_NAME<extension>')
parser.add_argument('-w', '--woeid', dest='woeid',
        default='12792014', help='WOEID')
parser.add_argument('-i', '--image-dir', dest='image_dir',
        default='/usr/local/geektool/tmp', help='Directory to store images')
parser.add_argument('-n', '--image-name', dest='image_name',
        default='yw-current-large', help='Image base name')
parser.add_argument('-u', '--units', dest='units', choices=['f','c'],
        default='f', help='Units f or c')
parser.add_argument('-d', '--debug', action='store_true', dest='debug',
        default=False)
args = parser.parse_args()

uri = 'http://weather.yahooapis.com/forecastrss?%s'
params = urllib.urlencode({'w':args.woeid, 'u':args.units})
url = uri % params

soup = BeautifulStoneSoup(urllib.urlopen(url), parseOnlyThese=SoupStrainer('item'))

item = soup.find('item')
link = item.link.string.split('*')

new_soup = BeautifulSoup(urllib.urlopen(link[1]), 
                    parseOnlyThese=SoupStrainer('div'))
icon_div = new_soup.find('div', attrs={'class': 'forecast-icon'})

quoted_re = re.compile("src='([^']*)'")
for p in re.split('\s*;\s*', icon_div['style']):
    if p.startswith('filter:progid:DXImageTransform.Microsoft.AlphaImageLoader'):
        imgurl = quoted_re.search(p).group(1)

if not imgurl:
    exit(1)

basename, extension = os.path.splitext(imgurl)
output_file = '%s/%s%s' % (args.image_dir, args.image_name, extension)
if args.debug:
    print 'Retrieve %s to %s' % (imgurl, output_file)
(filename, headers) = urllib.urlretrieve(imgurl, output_file)
