#!/opt/local/bin/python2.7
'''Get NHL Scores from ESPN'''

import re
import sys
import urllib
import os
from datetime import time, datetime, date, timedelta
from ConfigParser import SafeConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from BeautifulSoup import BeautifulSoup, SoupStrainer
from PIL import Image, ImageFont
from pytz import timezone

# ESPN reports time in ET
eastern = timezone('US/Eastern')

#-------------------------------------------------------------------------------

def one_of(*args):
    for i in args:
        if i:
            return i
    return None

def normalize(string):
    return re.subn('[^a-z]', '', string.lower())[0]

class Team():
    
    def __init__(self, name, score=None, record=None, image=None):

        self.name = name
        self.score = score
        self.record = record
        self.image = image

    def __str__(self):

        info = []
        info.append('<Team')
        info.append('name="%s"' % self.name)
        info.append('score="%s"' % self.score)
        info.append('record="%s"' % self.record)
        info.append('image="%s"' % self.image)

        return " ".join(info)

class Game():

    def __init__(self, type, away_team, home_team, status=None, remaining=None, headline=None, time=None, tv=None, lastplay=None):

        self.type = type
        self.away_team = away_team
        self.home_team = home_team
        self.status = status
        self.remaining = remaining
        self.headline = headline
        self.time = time
        self.tv = tv
        self.lastplay = lastplay

    def __str__(self):

        info = []
        info.append('<Game')
        info.append('type="%s"' % self.type)
        info.append('away_team="%s"' % self.away_team)
        info.append('home_team="%s"' % self.home_team)
        info.append('status="%s"' % self.status)
        info.append('time="%s"' % self.time)
        info.append('remaining="%s"' % self.remaining)
        info.append('headline="%s"' % self.headline)
        info.append('tv="%s"' % self.tv)
        info.append('lastplay="%s"' % self.lastplay)
        info.append('>')

        return " ".join(info)

#-------------------------------------------------------------------------------

def find_time_remaining(game_block):
    remaining_block = game_block.find('span', 'time-remaining')

    if remaining_block:
        remaining = remaining_block.text.replace('&nbsp;', '')
    else:
        remaining = None

    return remaining

def find_headline(game_block):
    headline_block = game_block.find('div', 'recap-headline')

    if headline_block.contents:
        headline = headline_block.a.text.replace('&nbsp;', '')
    else:
        headline = None

    return headline

def find_lastplay(game_block):
    lastplay_block = g.find('span', id = re.compile('-lastPlayText$'))

    if lastplay_block:
        lastplay = lastplay_block.string.replace('&nbsp;', '')
    else:
        lastplay = None

    return lastplay

def format_record(record, f):
    '''Reformat the team record using a passed format string expecting the keys w, l, s and p'''
    record_re = re.compile('\((\d+)-(\d+)-(\d+),\s+(\d+) pts\)')
    m = record_re.match(record)
    k = ('w', 'l', 's', 'p')
    fk = dict(zip(k, m.groups()))
    return f.format(**fk)

def find_team_info(game_header, boxid, homeaway):
    header = game_header.find('tr', id='%s-%sHeader' % (boxid, homeaway))

    name_block = header.find('td', 'team-name')
    name = name_block.div.a.text

    score_block = header.find('span', id='%s-%sHeaderScore' % (boxid, homeaway))
    score = score_block.text

    next = header.nextSibling
    record = next.td.text.replace('&nbsp;', '')

    return (name, score, record)


#-------------------------------------------------------------------------------

def get_font(name, args, default_font):

    try:
        font = ImageFont.truetype(args[name + '.font'], int(args[name + '.fontsize']))
    except:
        font = default_font

    return font

def get_color(name, args, default_color):

    property = name + '.color'

    if property in args:
        color = args[property]
    else:
        color = default_color

    return color


#-------------------------------------------------------------------------------

conf_parser = ArgumentParser(add_help=False)
conf_parser.add_argument('-f', '--config-file', dest='config_file', metavar='FILE',
        help='Config file to load')
conf_parser.add_argument('-s', '--section',  dest='section', default='nhl',
        help='Section of Config File to use')
args, remaining_argv = conf_parser.parse_known_args()

parser = ArgumentParser(parents=[conf_parser],
        description=__doc__,
        formatter_class=ArgumentDefaultsHelpFormatter)

parser.add_argument('--font', dest='font', help='TrueType Font to Load')
parser.add_argument('--fontsize', dest='fontsize', type=int, help='Font Size')
parser.add_argument('--fontcolor', dest='fontcolor', help='Font Color (PIL)')
parser.add_argument('-d', '--date', dest='date', metavar='YYYYMMDD', help='Specific date')
parser.add_argument('--spacing', dest='spacing', type=int, help='Spacing between Logos')
parser.add_argument('--hpad', dest='hpadding', type=int, help='Horizontal Montage Spacing')
parser.add_argument('--vpad', dest='vpadding', type=int, help='Vertical Montage Spacing')
parser.add_argument('-V', '--vertical', dest='vertical', metavar='FILE', help='Vertical Montage File Name')
parser.add_argument('-H', '--horizontal', dest='horizontal', metavar='FILE', help='Horizontal Montage File Name')
parser.add_argument('-S', '--slideshow', dest='slideshow', metavar='DIR', help='Slideshow Directory')
parser.add_argument('-l', '--headline', dest='headline', action='store_true',
        help='Display headline')
parser.add_argument('-q', '--quarters', dest='quarters', action='store_true',
        help='Display quarter scores')
parser.add_argument('-g', '--desaturate', dest='desaturate', default=False, action='store_true',
        help='Desaturate the image')
parser.add_argument('--prefix', dest='prefix', default='nhl-game-', help='File Name Prefix')
parser.add_argument('--timestamp', dest='timestamp', action='store_true', default=False,
        help='Add a timestamp to the image')
parser.add_argument('--timestamp-format', dest='timestamp_format', default='%m/%d %H:%M',
        help='Format for timestamp (strftime)')
parser.add_argument('--timezone', dest='timezone', default='US/Central', help='Local timezone')

parser.add_argument('--date-format', dest='date_format', default='%l:%M %p',
        help='Format for date for game time (strftime)')
parser.add_argument('--record-format', dest='record_format', default='{w}-{l}-{s} ({p})', help='Team Record format')
parser.add_argument('-y', '--yesterday', dest='yesterday', action='store_true', default=False,
        help='Get scores from yesterday')

parser.add_argument('-L', '--libdir', dest='libdir', metavar='DIR', 
        help='imageutils.py directory to search before "__file__/../lib"')

if args.config_file:
    config = SafeConfigParser()
    config.read(args.config_file)
    defaults = dict(config.items(args.section))
    parser.set_defaults(**defaults)

args = parser.parse_args()
vargs = vars(args)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
if args.libdir:
    sys.path.insert(0, args.libdir)
from imageutils import horizontal_montage, vertical_montage, text_as_image, drop_shadow

localtz = timezone(args.timezone)

gamebox_re = re.compile('\d+-gamebox')
game_header_re = re.compile('\s*game-header\s*')
date_re = re.compile('(\d+):(\d+) ([AP]M) ET')

game_time_re = re.compile('(\d+):(\d+) ([AP]M) ET')

url = 'http://scores.espn.go.com/nhl/scoreboard'
if args.date:
    url = url + '?' + urllib.urlencode({ 'date': args.date })

if args.yesterday:
    yesterday = localtz.localize(datetime.now()) - timedelta(1)
    date_str = yesterday.strftime('%Y%m%d')
    url = url + '?' + urllib.urlencode({ 'date': date_str })

gameboxes = SoupStrainer('div', id=gamebox_re)
html = urllib.urlopen(url).read()

soup = BeautifulSoup(html, parseOnlyThese=gameboxes)


def get_team(header, boxid, homeaway, args):
    (name, score, record) = find_team_info(game_header, boxid, homeaway)

    image = Image.open(args['image.' + normalize(name)])

    return Team(name, score=score, record=record, image=image)

games = []
for g in soup.contents:
    # print g.prettify()
    boxid = g['id'].split('-')[0]
    type = g['class'].split(" ")[3]

    header = g.find('div', id='%s-gameHeader' % boxid)
    [game_header, game_info] = header.contents[0:2]

    away_team  = get_team(game_header, boxid, 'away', vargs)
    home_team  = get_team(game_header, boxid, 'home', vargs)

    # Game Info

    tv = None
    game_time = None
    if type == 'pregame':
        network_block = game_info.find('li', id='%s-statusLine1' % boxid)
        tv = network_block.text.replace('&nbsp;','')

        time_block = game_info.find('span', id='%s-statusLine2Left' % boxid)
        
        upcoming = game_time_re.match(time_block.text)
        hour = int(upcoming.group(1))
        minute = int(upcoming.group(2))
        ampm = upcoming.group(3)
        if ampm == 'PM' and int(hour) < 12:
            hour = hour + 12
        game_time = datetime.combine(date.today(), time(hour, minute, tzinfo=eastern)).astimezone(localtz)

    elif type == 'final':
        status_block = game_info.find('li', id='%s-statusLine1' % boxid)

    status = []
    status.append(game_info.contents[0].text.replace('&nbsp;',''))
    status.append(game_info.contents[1].contents[0].text.replace('&nbsp;',''))
    status.append(game_info.contents[1].contents[1].text.replace('&nbsp;',''))

    remaining = find_time_remaining(g)
    headline = find_headline(g)
    lastplay = find_lastplay(g)

    game = Game(type, away_team, home_team, remaining=remaining, time=game_time, 
            headline=headline, status=status, tv=tv, lastplay=lastplay)
    games.append(game)

fonts = {}
try:
    fonts['default'] = ImageFont.truetype(args.font, args.fontsize)
except:
    print >>sys.stderr, "Unable to load font or no font specified"
    fonts['default'] = ImageFont.load_default()

colors = {}
colors['default'] = args.fontcolor

for s in ('record', 'headline', 'lastplay', 'tv', 'date', 'timestamp', 'score', 'status', 'gametime', 'countdown'):
    fonts[s] = get_font(s, vargs, fonts['default'])
    colors[s] = get_color(s, vargs, colors['default'])

images = []
for i, game in enumerate(games):
    im = []

    # Team images
    away_image = game.away_team.image
    home_image = game.home_team.image

    # Display the teams record if it is pre-game
    if game.type == 'pregame':

        ari = text_as_image(format_record(game.away_team.record, args.record_format), font=fonts['record'], fill=colors['record'])
        away_image = vertical_montage([away_image, ari], halign='center')

        hri = text_as_image(format_record(game.home_team.record, args.record_format), font=fonts['record'], fill=colors['record'])
        home_image = vertical_montage([home_image, hri], halign='center')

    # Team Icons
    icons = horizontal_montage([away_image, home_image], spacing=args.spacing)
    im.append(icons)

    (iw, ih) = icons.size

    if game.type == 'final':
        # Display the current/final score
        away_si = text_as_image("%s" % game.away_team.score, font=fonts['score'], fill=colors['score'])
        home_si = text_as_image("%s" % game.home_team.score, font=fonts['score'], fill=colors['score'])
        score_i = horizontal_montage([away_si, home_si], min_width=iw/2, valign='center', halign='center')
        im.append(score_i)

        im.append(text_as_image(game.status[0].upper(), font=fonts['status'], fill=colors['status']))
         

    # Display some game info
    elif game.type == 'in-progress':
        # Display the current score and game status
        away_si = text_as_image("%s" % game.away_team.score, font=fonts['score'], fill=colors['score'])
        home_si = text_as_image("%s" % game.home_team.score, font=fonts['score'], fill=colors['score'])
        score_i = horizontal_montage([away_si, home_si], min_width=iw/2, valign='center', halign='center')
        im.append(score_i)

        im.append(text_as_image("%s %s" % (game.status[2].upper(), game.status[1].upper().replace(',','')), font=fonts['status'], fill=colors['status']))
        #if game.lastplay:
        #    im.append(text_as_image(game.lastplay, font=fonts['lastplay'], fill=fontcolor))

    elif game.type == 'pregame':
        # Display when the game will take place and the tv network

        date_str = game.time.strftime(args.date_format)

        countdown = game.time - localtz.localize(datetime.now())
        datecolor = colors['gametime']
        if countdown.total_seconds() < 900:
            datecolor = colors['countdown']

        im.append(text_as_image(date_str, font=fonts['gametime'], fill=datecolor))

#       countdown = game.time - localtz.localize(datetime.now())
#       if countdown.total_seconds() < 3600:
#           minutes = countdown.total_seconds() / 60
#           seconds = countdown.total_seconds() - (minutes * 60)
#           im.append(text_as_image('%02d:%02d' % (minutes, seconds), font=fonts['countdown'], fill=colors['countdown']))

        if game.tv:
            im.append(text_as_image(game.tv, font=fonts['tv'], fill=colors['tv']))
        
    image = drop_shadow(vertical_montage(im, spacing=0, halign='center'))
    images.append(image)

if args.slideshow:
    if not os.path.exists(args.slideshow):
        os.makedirs(args.slideshow)

    # Clean the directory
    for file in os.listdir(args.slideshow):
        if file.startswith(args.prefix):
            os.remove(os.path.join(args.slideshow, file))
    
    # Save all the files
    for i, image in enumerate(images):
        filename = os.path.join(args.slideshow, '%s%02d.png' % (args.prefix, i))
        image.save(filename)


if args.timestamp:
    now = localtz.localize(datetime.now())
    now_image = text_as_image(now.strftime(args.timestamp_format), font=fonts['timestamp'], fill=colors['timestamp'])

if args.vertical:
    montage = vertical_montage(images, spacing=max(args.vpadding,0), halign='center', valign='center')
    if args.timestamp:
        montage = vertical_montage([montage, now_image], halign='center', valign='bottom')
    dir = os.path.dirname(args.vertical)
    if not os.path.exists(dir):
        os.makedirs(dir)

    montage.save(args.vertical)

if args.horizontal:
    montage = horizontal_montage(images, spacing=max(args.hpadding,0), halign='center', valign='top')
    if args.timestamp:
        montage = horizontal_montage([now_image.rotate(90), montage], spacing=1, valign='center')
    dir = os.path.dirname(args.horizontal)
    if not os.path.exists(dir):
        os.makedirs(dir)
    montage.save(args.horizontal)
