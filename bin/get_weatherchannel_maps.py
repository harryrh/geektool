#!/opt/local/bin/python2.7

#
# Grab a bunch of images and throw them in a directory for GeekTool to find
#
# Config file has a named section from the arguments and picks up any
# properties starting with image* as a url to grab
#
# Requires Python 2.6 or 2.7 and BeautifulSoup
#
# [section]
# path = directory-to-save
# image_X = url1
# image_Y = url2
#

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from ConfigParser import SafeConfigParser
import urllib
import os
import shlex
from BeautifulSoup import BeautifulSoup
import threading

MAX_JOBS=10

#
# Get a Weather Channel URL, find an image reference with a specific
# name attribute then retrieve that image to the output directory
#
def get_image(url, name, output_dir):
    try:
        html = urllib.urlopen(url).read()
    except IOError as (errno, strerror):
        print 'I/O error({0}): {1}'.format(errno, strerror)
        exit(1)

    soup = BeautifulSoup(html)
    map_tag = soup.find('img', attrs = { 'name': name})
    map_url = map_tag['src']

    (head, tail) = os.path.split(map_url)
    dest = '%s/%s' % (output_dir, tail)
    try:
        urllib.urlretrieve(map_url, dest)
    except urllib.ContentTooShortError as err:
        print 'Content too short (expected %s bytes and served %s)' % (err.expected, err.downloaded)
        exit(1)
    except IOError as (errno, strerror):
        print 'I/O error({0}): {1}'.format(errno, strerror)
        exit(1)

conf_parser = ArgumentParser(add_help=False)
conf_parser.add_argument('-f', '--config-file', dest='config_file', metavar='FILE',
        help='Config file to load')
conf_parser.add_argument('-s', '--section',  dest='section', default='maps',
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

parser.add_argument('-o', '--output-dir', dest='output_dir',
        default='/usr/local/geektool/tmp/wc-maps', help='Directory to store map images')
parser.add_argument('-n', '--image-name', dest='image_name',
        default='mapImg', help='<img name="name"> attribute to search for')
args = parser.parse_args()
vargs = vars(args)

urls = shlex.split(args.urls)

if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)
else:
    # Clean the directory
    for file in os.listdir(args.output_dir):
        os.remove(os.path.join(args.output_dir, file))

for url in urls:
    t = threading.Thread(target=get_image, args=(url, args.image_name, args.output_dir))
    t.start()
