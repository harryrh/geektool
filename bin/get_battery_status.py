#!/opt/local/bin/python2.7
'''Determine the battery status of Apple Bluetooth Connected devices -- print status, or generate an image'''

# An image is generated by copying a file from a directory
# of files that have the possible status for the battery.
# This file is copied to a static name based on the device
# in a target directory
#
# [battery]
# icondir = /usr/local/geektool/images/battery
# 
# disconnected = %(icondir)s/disconnected.png
# 
# status.0   = %(icondir)s/discharging_000.png
# status.20  = %(icondir)s/discharging_020.png
# status.40  = %(icondir)s/discharging_040.png
# status.60  = %(icondir)s/discharging_060.png
# status.80  = %(icondir)s/discharging_080.png
# status.100 = %(icondir)s/discharging_100.png
#
# e.g.
# ./get_battery_status.py print mouse
#   -- Print the percent
# ./get_battery_status.py -f /usr/local/geektool/etc/battery.ini image mouse0
#   -- Copy an image to represent the status
#

import sys
import os

from subprocess import Popen, PIPE
from ConfigParser import SafeConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

devices = {
    'mouse'   : 'BNBMouseDevice',
    'trackpad': 'BNBTrackpadDevice',
    'keyboard': 'AppleBluetoothHIDKeyboard' }


conf_parser = ArgumentParser(add_help=False)
conf_parser.add_argument('-f', '--config-file', dest='config_file', metavar='FILE',
        help='Config file to load')
conf_parser.add_argument('-s', '--section',  dest='section', default='battery',
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

subparsers = parser.add_subparsers(help='sub-commands')

# print sub-command
parser_print = subparsers.add_parser('print', help='print the battery status',
        formatter_class=ArgumentDefaultsHelpFormatter)
parser_print.add_argument('-p', '--prefix', dest='prefix', 
        default='', help='String to print before battery percentage')
parser_print.add_argument('-s', '--suffix', dest='suffix', 
        default='%', help='String to print after battery percentage')
parser_print.add_argument('-t', '--template', action='store', dest='template', 
        default='{prefix}{percent}{suffix}', help='Specify the print format template')
parser_print.set_defaults(command='print')

# image sub-command
parser_image = subparsers.add_parser('image', help='generate the image file',
        formatter_class=ArgumentDefaultsHelpFormatter)
parser_image.add_argument('-i', '--image-dir', dest='image_dir', metavar='DIRECTORY',
        default='/usr/local/geektool/tmp', help='Directory to store image')
parser_image.add_argument('-d', '--desaturate', dest='desaturate',
        default=False, action='store_true', help='Desaturate the image')
parser_image.add_argument('-r', '--rotate', dest='rotate', type=int, metavar='DEGREES',
        default=0, help='Rotate the image counter-clockwise degrees')
parser_image.set_defaults(command='image')

parser.add_argument('device', choices=devices.keys(), help='The device to query')

args = parser.parse_args()
vargs = vars(args)

# Find the 'status.N' items
icons = []
if args.config_file:
    config = SafeConfigParser()
    config.read(args.config_file)
    for name in vargs:
        if name.startswith('status.'):
            status = int(name.replace('status.',''))
            icons.append((status, vargs[name])) 

which = devices[args.device]

# Find the percent
ioreg_p = Popen(['/usr/sbin/ioreg', '-c', which], stdout=PIPE)
grep_p = Popen(['/usr/bin/grep', 'BatteryPercent'], stdin=ioreg_p.stdout, stdout=PIPE)
tail_p = Popen(['/usr/bin/tail','-n','1'], stdin=grep_p.stdout, stdout=PIPE)
awk_p = Popen(['/usr/bin/awk', '{ print $NF }'], stdin=tail_p.stdout, stdout=PIPE)

try:
    percent = int(awk_p.communicate()[0])
except ValueError: # Disconnected
    percent = -1

# Print the status and exit
if args.command == 'print':
    if percent >= 0:
        print args.template.format(percent=percent, prefix=args.prefix, suffix=args.suffix)
    sys.exit(0)

from PIL import Image

# Generate the image
if percent < 0: # Disconnected
    icon = vargs['disconnected']
else:
    # Look for the image with the largest number greater than the status
    for (max, icon) in sorted(icons, cmp=lambda x,y: cmp(x[0],y[0])):
        if percent <= max:
            break

(root, ext) = os.path.splitext(icon)
dest = '%s/battery-status-%s%s' % (args.image_dir, args.device, ext)

im = Image.open(icon)

if args.desaturate:
    im = im.convert('LA')

if args.rotate:
    im = im.rotate(args.rotate)

im.save(dest)