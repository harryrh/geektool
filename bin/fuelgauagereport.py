#!/opt/local/bin/python2.7

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup, SoupStrainer
import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from urllib import urlopen


parser = ArgumentParser(description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('state', help='Two letter state')
parser.add_argument('city', help='City')
parser.add_argument('fuel', choices=['Regular', 'Mid', 'Premium', 'Diesel'], help='Fuel type')
args = parser.parse_args()

url = 'http://fuelgaugereport.opisnet.com/%smetro.asp' % args.state
html = urlopen(url).read()

strainer = SoupStrainer('table')
soup = BeautifulSoup(html, parseOnlyThese=strainer)

cities = {}

for table in soup.contents:
    tr_b = table.findAll('tr')

    header = tr_b[0]
    current = tr_b[1]

    city = header.find('td').text
    paren = city.find(' (')
    if paren > 0:
        city = city[0:paren]

    headers = [td.text for td in header.findAll('td')[1:]]
    prices = [td.text for td in current.findAll('td')[1:]]

    cities[city] = dict(zip(headers, prices))

if args.city not in cities:
    print 'No City "%s"' % args.city
    print >>sys.stderr, ', '.join(cities.keys())
    exit(1)

print cities[args.city][args.fuel]
