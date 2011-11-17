#!/opt/local/bin/python2.7
'''Get stock prices from Yahoo! and print in a defined format'''

codes = '''Codes:
    a   Ask
    a2  Average Daily Volume
    a5  Ask Size
    b   Bid
    b2  Ask (Real-time)
    b3  Bid (Real-time)
    b4  Book Value
    b6  Bid Size
    c   Change & Percent Change
    c1  Change
    c3  Commission  c6  Change (Real-time)
    c8  After Hours Change (Real-time)
    d   Dividend/Share
    d1  Last Trade Date
    d2  Trade Date
    e   Earnings/Share
    e1  Error Indication (returned for symbol changed / invalid)
    e7  EPS Estimate Current Year
    e8  EPS Estimate Next Year
    e9  EPS Estimate Next Quarter
    f6  Float Shares
    g   Day's Low
    h   Day's High
    j   52-week Low
    k   52-week High
    g1  Holdings Gain Percent
    g3  Annualized Gain
    g4  Holdings Gain
    g5  Holdings Gain Percent (Real-time)
    g6  Holdings Gain (Real-time)
    i   More Info
    i5  Order Book (Real-time)
    j1  Market Capitalization
    j3  Market Cap (Real-time)
    j4  EBITDA
    j5  Change From 52-week Low
    j6  Percent Change From 52-week Low
    k1  Last Trade (Real-time) With Time
    k2  Change Percent (Real-time)
    k3  Last Trade Size
    k4  Change From 52-week High
    k5  Percent Change From 52-week High
    l   Last Trade (With Time)
    l1  Last Trade (Price Only)
    l2  High Limit
    l3  Low Limit
    m   Day's Range
    m2  Day's Range (Real-time)
    m3  50-day Moving Average
    m4  200-day Moving Average
    m5  Change From 200-day Moving Average
    m6  Percent Change From 200-day Moving Average
    m7  Change From 50-day Moving Average
    m8  Percent Change From 50-day Moving Average
    n   Name
    n4  Notes
    o   Open
    p   Previous Close
    p1  Price Paid
    p2  Change in Percent
    p5  Price/Sales
    p6  Price/Book
    q   Ex-Dividend Date
    r   P/E Ratio
    r1  Dividend Pay Date
    r2  P/E Ratio (Real-time)
    r5  PEG Ratio
    r6  Price/EPS Estimate Current Year
    r7  Price/EPS Estimate Next Year
    s   Symbol
    s1  Shares Owned
    s7  Short Ratio
    t1  Last Trade Time
    t6  Trade Links
    t7  Ticker Trend
    t8  1 yr Target Price
    v   Volume
    v1  Holdings Value
    v7  Holdings Value (Real-time)
    w   52-week Range
    w1  Day's Value Change
    w4  Day's Value Change (Real-time)
    x   Stock Exchange
    y   Dividend Yield      
'''

import sys
import urllib
import csv
import shlex
from ConfigParser import SafeConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

conf_parser = ArgumentParser(add_help=False)
conf_parser.add_argument('-f', '--config-file', dest='config_file', metavar='FILE',
        help='Config file to load')
conf_parser.add_argument('-s', '--section',  dest='section', default='stocks',
        help='Section of Config File to use')
conf_parser.add_argument('--help-codes', action='store_true', dest='help_codes', default=False,
        help='Display codes and exit')
args, remaining_argv = conf_parser.parse_known_args()

if args.help_codes:
    print codes
    sys.exit(0)

parser = ArgumentParser(parents=[conf_parser],
        description=__doc__,
        formatter_class=ArgumentDefaultsHelpFormatter)

if args.config_file:
    config = SafeConfigParser()
    config.read(args.config_file)
    defaults = dict(config.items(args.section))
    parser.set_defaults(**defaults)

parser.add_argument('-j', '--join', dest='join', default='|', help='Join Character', metavar='STRING')
parser.add_argument('-F', '--format', dest='format', help='Output format')
parser.add_argument('-S', '--symbol', dest='symbols',
        help='Specify stock symbols -- space separated list')
parser.add_argument('-l', '--line-join', dest='linejoin', default='\n', help='Join Lines')
parser.add_argument('codes', default='s', help='Code string')
args = parser.parse_args()
vargs = vars(args)

symbols = shlex.split(args.symbols)

uri = 'http://download.finance.yahoo.com/d/quotes.csv?%s'
params = {
    's': ' '.join(symbols),
    'f': args.codes,
    'e': '.csv'}
url = uri % urllib.urlencode(params)

stockReader = csv.reader(urllib.urlopen(url))
lines = []
for row in stockReader:
    if args.format:
        line = args.format % tuple(row)
    else:
        line = args.join.join(row)
    lines.append(line)

print args.linejoin.join(lines)
