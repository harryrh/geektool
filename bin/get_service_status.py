#!/opt/local/bin/python2.7
'''Get status of anything'''

from subprocess import check_output, CalledProcessError
from PIL import Image, ImageOps
import sys
import shlex
from ConfigParser import SafeConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os

conf_parser = ArgumentParser(add_help=False)
conf_parser.add_argument('-f', '--config-file', dest='config_file', metavar='FILE',
        help='Config file to load')
conf_parser.add_argument('-s', '--section',  dest='section', default='status',
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

parser.add_argument('-H', dest='horizontal_image', metavar='FILE',
        help='File name for horizontal image')
parser.add_argument('-V', dest='vertical_image', metavar='FILE',
        help='File name for vertical image')
parser.add_argument('-i', '--invert', dest='invert', action='store_true',
        default=False, help='Invert assumes grayscale')
parser.add_argument('-g', '--grayscale', dest='grayscale', action='store_true',
        default=False, help='Convert output image to grayscale')
parser.add_argument('-L', '--libdir', dest='libdir', help='imageutils directory')

args = parser.parse_args()
vargs = vars(args)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
if args.libdir:
    sys.path.insert(0, args.libdir)
from imageutils import horizontal_montage, vertical_montage, drop_shadow

services = shlex.split(args.services)

up   = args.up
down = args.down

up_image   = Image.open(up).convert('RGBA')
down_image = Image.open(down).convert('RGBA')

up_alpha   = up_image.split()[3]
down_alpha = down_image.split()[3]

if args.invert:
    up_image = ImageOps.invert(ImageOps.grayscale(up_image)).convert('RGBA')
    down_image = ImageOps.invert(ImageOps.grayscale(down_image)).convert('RGBA')
    up_image.putalpha(up_alpha)
    down_image.putalpha(down_alpha)

if args.grayscale:
    up_image = ImageOps.grayscale(up_image).convert('RGBA')
    down_image = ImageOps.grayscale(down_image).convert('RGBA')
    up_image.putalpha(up_alpha)
    down_image.putalpha(down_alpha)

images = []
for service in services:
    command = vargs['check.' + service]
    try:
        output = check_output(command, shell=True)
        images.append(up_image)
    except CalledProcessError as e:
        images.append(down_image)

if args.horizontal:
    hm = drop_shadow(horizontal_montage(images, valign='top'))
    hm.save(args.horizontal)

if args.vertical:
    vm = drop_shadow(vertical_montage(images, valign='center'))
    vm.save(args.vertical)

