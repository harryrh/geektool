#!/opt/local/bin/python2.7
'''Get NHL Scores from ESPN'''

from BeautifulSoup import BeautifulSoup, SoupStrainer
from ConfigParser import SafeConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import re
import sys
import urllib
import os
from datetime import time, datetime, date

from PIL import Image, ImageFont

from pytz import timezone

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

def find_team_info(blocks):
    name   = blocks[0].contents[0].a.text
    score  = blocks[0].contents[1].span.text.replace('&nbsp;','')
    record = blocks[1].contents[0].contents[1]

    return (name, score, record)

#-------------------------------------------------------------------------------

def get_font(name, args, default_font):
    try:
        font = ImageFont.truetype(args[name + '.font'], int(args[name + '.fontsize']))
    except:
        font = default_font

    return font

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
parser.add_argument('-V', '--vertical', dest='vertical', help='Vertical Montage File Name')
parser.add_argument('-H', '--horizontal', dest='horizontal', help='Horizontal Montage File Name')
parser.add_argument('-S', '--slideshow', dest='slideshow', help='Slideshow Directory')
parser.add_argument('-l', '--headline', dest='headline', action='store_true',
        help='Display headline')
parser.add_argument('-q', '--quarters', dest='quarters', action='store_true',
        help='Display quarter scores')
parser.add_argument('-g', '--desaturate', dest='desaturate', default=False, action='store_true',
        help='Desaturate the image')
parser.add_argument('-L', '--libdir', dest='libdir', metavar='DIR', help='imageutils directory')
parser.add_argument('--date-format', dest='date_format', default='%l:%M %p %Z',
        help='Adjust Gametime by hours')
parser.add_argument('--prefix', dest='prefix', default='nhl-game-', help='File Name Prefix')

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
from imageutils import horizontal_montage, vertical_montage, text_as_image

try:
    localtz = timezone(args.tz)
except:
    localtz = eastern

gamebox_re = re.compile('\d+-gamebox')
game_header_re = re.compile('\s*game-header\s*')
date_re = re.compile('(\d+):(\d+) ([AP]M) ET')

url = 'http://scores.espn.go.com/nhl/scoreboard'
if args.date:
    url = url + '?' + urllib.urlencode({ 'date': args.date })

gameboxes = SoupStrainer('div', id=gamebox_re)
soup = BeautifulSoup(urllib.urlopen(url).read(), parseOnlyThese=gameboxes)

games = []
for g in soup.contents:
    status = []
    type = g['class'].split(" ")[3]
    header = g.find('div', attrs = { 'class': game_header_re })

    [game_header, game_info] = header.contents[0:2]

    # Teams Info

    (away_name, away_score, away_record) = find_team_info(game_header.contents[0].contents[0:2])
    away_image = Image.open(vargs['image.' + normalize(away_name)]).convert('RGBA')

    away_team  = Team(away_name, score=away_score, record=away_record, image=away_image)

    (home_name, home_score, home_record) = find_team_info(game_header.contents[0].contents[2:4])
    home_image = Image.open(vargs['image.' + normalize(home_name)]).convert('RGBA')

    home_team  = Team(home_name, score=home_score, record=home_record, image=home_image)

    # Game Info

    status.append(game_info.contents[0].text.replace('&nbsp;',''))
    status.append(game_info.contents[1].contents[0].text.replace('&nbsp;',''))
    status.append(game_info.contents[1].contents[1].text.replace('&nbsp;',''))

    tv = None
    game_time = None
    if type == 'pregame':
        tv = status[0]
        upcoming = date_re.match(status[1])
        if upcoming:
            hour = int(upcoming.group(1))
            minute = int(upcoming.group(2))
            ampm = upcoming.group(3)
            if ampm == 'PM' and int(hour) < 12:
                hour = hour + 12
            game_time = datetime.combine(date.today(), time(hour, minute, tzinfo=eastern)).astimezone(localtz)

    remaining = find_time_remaining(g)
    headline = find_headline(g)
    lastplay = find_lastplay(g)

    game = Game(type, away_team, home_team, remaining=remaining, time=game_time, 
            headline=headline, status=status, tv=tv, lastplay=lastplay)
    games.append(game)

try:
    font = ImageFont.truetype(args.font, args.fontsize)
except:
    print >>sys.stderr, "Unable to load font or no font specified"
    font = ImageFont.load_default()

record_font = get_font('record', vargs, font)
headline_font = get_font('headline', vargs, font)
lastplay_font = get_font('lastplay', vargs, font)
tv_font = get_font('tv', vargs, font)
date_font = get_font('date', vargs, font)

if args.fontcolor:
    fontcolor = args.fontcolor
else:
    fontcolor = 'white'

images = []
for i, game in enumerate(games):
    im = []

    # Team images
    away_image = game.away_team.image
    home_image = game.home_team.image

    # Display the teams record if it is pre-game
    if game.type == 'pregame':
        f = '{w}-{l}-{s} ({p})'

        ari = text_as_image(format_record(game.away_team.record, f), font=record_font, fill=fontcolor)
        away_image = vertical_montage([away_image, ari], halign='center')

        hri = text_as_image(format_record(game.home_team.record, f), font=record_font, fill=fontcolor)
        home_image = vertical_montage([home_image, hri], halign='center')

    # Team Icons
    im.append(horizontal_montage([away_image, home_image], spacing=args.spacing))


    if game.type == 'final':
        # Display the current/final score
        im.append(text_as_image("%s - %s" % (game.away_team.score, game.home_team.score), font=font, fill=fontcolor))
        # Display the game 'headline' if desired (Final only)
        if args.headline:
            im.append(text_as_image(game.headline, font=headline_font, fill=fontcolor))
        im.append(text_as_image(game.status[0], font=font, fill=fontcolor))

    # Display some game info
    elif game.type == 'in-progress':
        # Display the current score and game status
        im.append(text_as_image("%s - %s" % (game.away_team.score, game.home_team.score), font=font, fill=fontcolor))
        im.append(text_as_image("%s %s" % (game.status[1], game.status[2]), font=font, fill=fontcolor))
        #if game.lastplay:
        #    im.append(text_as_image(game.lastplay, font=lastplay_font, fill=fontcolor))

    elif game.type == 'pregame':
        # Display when the game will take place and the tv network
        im.append(text_as_image(game.time.strftime('%l:%M %p %Z'), font=date_font, fill=fontcolor))
        if game.tv:
            im.append(text_as_image(game.tv, font=tv_font, fill=fontcolor))
        
    image = vertical_montage(im, spacing=0, valign='center')
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
        filename = os.path.join(args.slideshow, '%s-%02d.png' % (args.prefix, i))
        image.save(filename)

if args.vertical:
    montage = vertical_montage(images, spacing=max(args.vpadding,0), halign='center', valign='center')
    montage.save(args.vertical)

if args.horizontal:
    montage = horizontal_montage(images, spacing=max(args.hpadding,0), halign='center', valign='top')
    montage.save(args.horizontal)
