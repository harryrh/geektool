#!/opt/local/bin/python2.7
'''Generate pie charts for disk usage'''

import pylab as pl 
from subprocess import Popen, PIPE
from ConfigParser import SafeConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import re


conf_parser = ArgumentParser(add_help=False)
conf_parser.add_argument('-f', '--config-file', dest='config_file', metavar='FILE',
        help='Config file to load')
conf_parser.add_argument('-s', '--section',  dest='section', default='disk-usage',
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

parser.add_argument('--used-color', dest='used_color',
        help='Color for used section of pie (pylab)')
parser.add_argument('--free-color', dest='free_color',
        help='Color for free section of pie (pylab)')
parser.add_argument('--height', dest='height', type=float,
        help='Image height')
parser.add_argument('--width', dest='width', type=float,
        help='Image width')

parser.add_argument('-V', '--vertical', dest='vertical', metavar='FILE', help='Vertical File Name')
parser.add_argument('-H', '--horizontal', dest='horizontal', metavar='FILE', help='Horizontal File Name')
args = parser.parse_args()
vargs = vars(args)

disks = re.split('\s*,\s*', args.disks)

df_p   = Popen(['/bin/df'] + disks , stdout=PIPE)
tail_p = Popen(['/usr/bin/tail', '-n', str(len(disks))], stdin=df_p.stdout, stdout=PIPE)

df_output = tail_p.communicate()[0].rstrip('\n\r')
usages = []
for line in df_output.split('\n'):
    usage = re.split('\s+', line, 5)
    usages.append(tuple(usage))

colors = [args.used_color, args.free_color]

# Put the pie charts in a row
if args.horizontal:
    # Horizonal 
    cols = len(disks)
    w = 1.0 / cols

    figheight = args.height
    figwidth = figheight * cols

    pl.figure(1, figsize=(figwidth, figheight))
    for i, usage in enumerate(usages):
        pl.axes([w*i, 0.0, w, 1.0])
        (patches, texts) = pl.pie(usage[2:4], explode=[0.1, 0], colors=colors, shadow=False)
        for wedge in patches:
            wedge.set_linewidth(0.0)
    pl.savefig(args.horizontal, transparent=True)

# Put the pie charts in a column
if args.vertical:
    # Vertical
    rows = len(disks)
    h = 1.0 / rows
    figwidth = args.width
    figheight = figwidth * rows

    pl.figure(2, figsize=(figwidth, figheight))
    for i, usage in enumerate(reversed(usages)):
        pl.axes([0.0, h*i, 1.0, h])
        (patches, texts) = pl.pie(usage[2:4], explode=[0.1, 0], colors=colors, shadow=False)
        for wedge in patches:
            wedge.set_linewidth(0.0)
    pl.savefig(args.vertical, transparent=True)

