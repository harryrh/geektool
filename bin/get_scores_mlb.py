#!/opt/local/bin/python2.7
'''Get NHL Scores from ESPN'''

import re
import sys
import urllib
import os
from datetime import time, datetime, date, timedelta
from ConfigParser import SafeConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

#from BeautifulSoup import BeautifulSoup, SoupStrainer
from bs4 import BeautifulSoup, SoupStrainer
from PIL import Image, ImageFont
from pytz import timezone

# ESPN reports time in ET
eastern = timezone('America/New_York')

#-------------------------------------------------------------------------------

def one_of(*args):
    for i in args:
        if i:
            return i
    return None

def normalize(string):
    return re.subn('[^a-z0-9]', '', string.lower())[0]

    return Team(name, record, runs=runs, hits=hits, errors=errors, image=image)

class Team():
    
    def __init__(self, name, record=None, runs=None, hits=None, errors=None, image=None):

        self.name = name
        self.record = record
        self.runs = runs
        self.hits = hits
        self.errors = errors
        self.image = image

    def __str__(self):

        info = []
        info.append('<Team')
        info.append('name="%s"' % self.name)
        info.append('record="%s"' % self.record)
        info.append('runs="%s"' % self.runs)
        info.append('hits="%s"' % self.hits)
        info.append('errors="%s"' % self.errors)
        info.append('image="%s"' % self.image)

        return " ".join(info)

class Game():

    def __init__(self, away_team, home_team, 
            status=None,
            time=None,
            tv=None,
            winning_pitcher=None,
            losing_pitcher=None,
            saving_pitcher=None, 
            current_pitcher=None,
            current_batter=None,
            lastplay=None):

        self.away_team = away_team
        self.home_team = home_team
        self.status = status
        self.time = time
        self.tv = tv
        self.winning_pitcher = winning_pitcher
        self.losing_pitcher = losing_pitcher
        self.saving_pitcher = saving_pitcher
        self.current_pitcher = current_pitcher
        self.current_batter = current_batter
        self.lastplay = lastplay

    def __str__(self):

        info = []
        info.append('<Game')
        info.append('away_team="%s"' % self.away_team)
        info.append('home_team="%s"' % self.home_team)
        info.append('status="%s"' % self.status)
        info.append('time="%s"' % self.time)
        info.append('tv="%s"' % self.tv)
        info.append('winning_pitcher="%s"' % self.winning_pitcher)
        info.append('losing_pitcher="%s"' % self.losing_pitcher)
        info.append('saving_pitcher="%s"' % self.saving_pitcher)
        info.append('current_batter="%s"' % self.current_batter)
        info.append('current_pitcher="%s"' % self.current_pitcher)
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
        try:
            lastplay = lastplay_block.string.replace('&nbsp;', '')
        except AttributeError:
            lastplay = None
    else:
        lastplay = None

    return lastplay

def format_record(record, f):
    '''Reformat the team record using a passed format string expecting the keys w, l, s and p'''
    record_re = re.compile('(\d+)-(\d+)')
    m = record_re.match(record)
    k = ('w', 'l')
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

def get_team_image(name, args):
    [source, x, y, w, h] = re.split('\s*,\s*', args['extract.%s' % name])

    im = Image.open(source)

    box = (int(x), int(y), int(x)+int(w), int(y)+int(h))

    return im.crop(box)

def get_team(block, boxid, homeaway, args):

    team_block = g.find('div', homeaway)

    tnb = team_block.find('p', 'team-name')
    name = tnb.contents[0].contents[0].string

    rb = team_block.find('p', 'record')
    record = rb.string.split(',')[0][1:]

    sb = team_block.find('ul', 'score')
    (runs, hits, errors) = (None, None, None)
    if sb:
        runs = sb.contents[0].string
        hits = sb.contents[1].string
        errors = sb.contents[2].string

    image = get_team_image(normalize(name), vargs)

    return Team(name, record, runs=runs, hits=hits, errors=errors, image=image)


def get_pitcher(block, boxid, pitcher):
    pitcher_b = g.find('span', id='%s-%s' % (boxid, pitcher))
    pitcher = None
    if pitcher_b:
        try:
            pitcher = '%s %s' % (pitcher_b.contents[1].string, pitcher_b.contents[2].replace('&nbsp;', ''))
        except IndexError:
            pass
        
    return pitcher


#-------------------------------------------------------------------------------

conf_parser = ArgumentParser(add_help=False)
conf_parser.add_argument('-f', '--config-file', dest='config_file', metavar='FILE',
        help='Config file to load')
conf_parser.add_argument('-s', '--section',  dest='section', default='mlb',
        help='Section of Config File to use')
args, remaining_argv = conf_parser.parse_known_args()

parser = ArgumentParser(parents=[conf_parser],
        description=__doc__,
        formatter_class=ArgumentDefaultsHelpFormatter)

parser.add_argument('--font', dest='font', help='TrueType Font to Load')
parser.add_argument('--fontsize', dest='fontsize', type=int, help='Font Size')
parser.add_argument('--fontcolor', dest='fontcolor', help='Font Color (PIL)')
parser.add_argument('-d', '--date', dest='date', metavar='YYYYMMDD',
        help='Specific date')
parser.add_argument('--spacing', dest='spacing', type=int,
        help='Spacing between Logos')
parser.add_argument('--hpad', dest='hpadding', type=int,
        help='Horizontal Montage Spacing')
parser.add_argument('--vpad', dest='vpadding', type=int,
        help='Vertical Montage Spacing')
parser.add_argument('-V', '--vertical', dest='vertical', metavar='FILE',
        help='Vertical Montage File Name')
parser.add_argument('-H', '--horizontal', dest='horizontal', metavar='FILE',
        help='Horizontal Montage File Name')
parser.add_argument('-S', '--slideshow', dest='slideshow', metavar='DIR',
        help='Slideshow Directory')
parser.add_argument('-l', '--headline', dest='headline', action='store_true',
        help='Display headline')
parser.add_argument('-q', '--quarters', dest='quarters', action='store_true',
        help='Display quarter scores')
parser.add_argument('-g', '--desaturate', dest='desaturate', default=False,
        action='store_true', help='Desaturate the image')
parser.add_argument('--prefix', dest='prefix', default='mlb-game-',
        help='File Name Prefix')
parser.add_argument('--timestamp', dest='timestamp', action='store_true',
        default=False, help='Add a timestamp to the image')
parser.add_argument('--timestamp-format', dest='timestamp_format',
        default='%m/%d %H:%M', help='Format for timestamp (strftime)')
parser.add_argument('--timezone', dest='timezone', default='US/Central',
        help='Local timezone')
parser.add_argument('--date-format', dest='date_format', default='%l:%M %p',
        help='Format for date for game time (strftime)')
parser.add_argument('--record-format', dest='record_format', default='{w}-{l}', help='Team Record format')
parser.add_argument('-y', '--yesterday', dest='yesterday', action='store_true',
        default=False, help='Get scores from yesterday')

parser.add_argument('--input-file', '-i', dest='input_file', default=None,
        help='Get HTML from a local file instead of the default location')


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

url = 'http://scores.espn.go.com/mlb/scoreboard'
if args.date:
    url = url + '?' + urllib.urlencode({ 'date': args.date })

if args.yesterday:
    yesterday = localtz.localize(datetime.now()) - timedelta(1)
    date_str = yesterday.strftime('%Y%m%d')
    url = url + '?' + urllib.urlencode({ 'date': date_str })

gameboxes = SoupStrainer('div', id=gamebox_re)

h2strainer = SoupStrainer('h2')

fonts = {}
colors = {}
try:
    fonts['default'] = ImageFont.truetype(args.font, args.fontsize)
except:
    fonts['default'] = ImageFont.load_default()

colors['default'] = args.fontcolor

for s in ('record', 'headline', 'lastplay', 'tv', 'date', 'timestamp', 'score', 'status', 'gametime', 'countdown'):
    fonts[s] = get_font(s, vargs, fonts['default'])
    colors[s] = get_color(s, vargs, colors['default'])

html = ''
if args.input_file:
    html = open(args.input_file).read()
else:
    html = urllib.urlopen(url).read()

h2soup = BeautifulSoup(html, parse_only=h2strainer)
print h2soup

exit(0)

soup = BeautifulSoup(html, parse_only=gameboxes)

games = []
for g in soup.contents[1:]:
    print g
    try:
        boxid = g['id'].split('-')[0]
    except TypeError:
        continue

    print boxid

    away_team = get_team(g, boxid, 'team away', vargs)
    home_team = get_team(g, boxid, 'team home', vargs)

    header_b = g.find('div', 'game-header')

    status_b = header_b.find('p', id='%s-statusLine1' % boxid)
    status = status_b.string

    upcoming = game_time_re.match(status)
    game_time = None
    if upcoming:
        hour = int(upcoming.group(1))
        minute = int(upcoming.group(2))
        ampm = upcoming.group(3)
        if ampm == 'PM' and int(hour) < 12:
            hour = hour + 12
        today = date.today()
        game_time = eastern.localize(datetime(today.year, today.month, today.day, hour, minute))
        game_time = localtz.normalize(game_time.astimezone(localtz))


    tv_b = header_b.find('div', id='%s-statusLine2' % boxid)
    tv = None
    if tv_b:
        tv = "".join(x.string for x in tv_b.contents[0].contents)
        tv = tv.replace('&nbsp;', '')

    winning_pitcher = get_pitcher(g, boxid, 'winningPitcher')
    losing_pitcher = get_pitcher(g, boxid, 'losingPitcher')
    saving_pitcher = get_pitcher(g, boxid, 'savingPitcher')

    cp_b = g.find('li', id='%s-currentPitcherName' % boxid)
    if cp_b:
        current_pitcher = cp_b.contents[0].string.replace('&nbsp;','').strip()

    cb_b = g.find('li', id='%s-currentBatterName' % boxid)
    if cb_b:
        current_batter = cb_b.contents[0].string.replace('&nbsp;','').strip()

    lpt_b = g.find('span', id='%s-lastPlayText' % boxid)
    if lpt_b:
        last_play_text = lpt_b.string.replace('&nbsp;', '').strip()

    game = Game(away_team, home_team, 
            status=status,
            time=game_time,
            tv=tv,
            winning_pitcher=winning_pitcher,
            losing_pitcher=losing_pitcher,
            saving_pitcher=saving_pitcher,
            current_pitcher=current_pitcher,
            current_batter=current_batter,
            lastplay=last_play_text)

    games.append(game)

#-----------------------------------------------------------------------------

time_re = re.compile('(\d+:\d+ [AP]M) [A-Z]{2}')

images = []
for i, game in enumerate(games):
    im = []

    # Team images
    away_image = game.away_team.image
    home_image = game.home_team.image

    upcoming = game_time_re.match(game.status)

    if upcoming:

        away_ri = text_as_image("%s" % game.away_team.record, font=fonts['record'], fill=colors['record'])
        home_ri = text_as_image("%s" % game.home_team.record, font=fonts['record'], fill=colors['record'])

        away_i = vertical_montage([away_image, away_ri], halign='left')
        home_i = vertical_montage([home_image, home_ri], halign='left')

        time_i = text_as_image(game.time.strftime("%I:%M %p"), font=fonts['gametime'], fill=colors['gametime'])
        tv_i = text_as_image(game.tv, font=fonts['tv'], fill=colors['tv'])

        im = horizontal_montage([away_i, home_i], halign='center')
    
        image = vertical_montage([im, time_i, tv_i], halign='center')
        images.append(image)

    # Final or in progress
    else:
        away_ri = text_as_image("%s" % game.away_team.runs, font=fonts['score'], fill=colors['score'])
        home_ri = text_as_image("%s" % game.home_team.runs, font=fonts['score'], fill=colors['score'])

        away_hi = text_as_image("%s" % game.away_team.hits, font=fonts['score'], fill=colors['score'])
        home_hi = text_as_image("%s" % game.home_team.hits, font=fonts['score'], fill=colors['score'])

        away_ei = text_as_image("%s" % game.away_team.errors, font=fonts['score'], fill=colors['score'])
        home_ei = text_as_image("%s" % game.home_team.errors, font=fonts['score'], fill=colors['score'])

        away_si = horizontal_montage([away_ri, away_hi, away_ei], halign='right', spacing=10)

        home_si = horizontal_montage([home_ri, home_hi, home_ei], halign='right', spacing=10)

        away_i = vertical_montage([away_image, away_ri], halign='center')
        home_i = vertical_montage([home_image, home_ri], halign='center')

        fm = []

        fm.append(horizontal_montage([away_i, home_i]))

        fm.append(text_as_image("%s" % game.status, font=fonts['status'], fill=colors['status']))
        if not game.status.startswith('End') and not game.status.startswith('Middle') and not game.status.startswith('Final'):
            fm.append(text_as_image("%s" % game.lastplay, font=fonts['lastplay'], fill=colors['lastplay']))

        if game.winning_pitcher:
            fm.append(text_as_image("W: %s" % game.winning_pitcher, 
                font=fonts['lastplay'], fill=colors['lastplay']))
        if game.losing_pitcher:
            fm.append(text_as_image("L: %s" % game.losing_pitcher,
                font=fonts['lastplay'], fill=colors['lastplay']))
        if game.saving_pitcher:
            fm.append(text_as_image("S: %s" % game.saving_pitcher,
                font=fonts['lastplay'], fill=colors['lastplay']))

        if game.current_batter:
            fm.append(text_as_image("B: %s" % game.current_batter,
                font=fonts['lastplay'], fill=colors['lastplay']))

        if game.current_pitcher:
            fm.append(text_as_image("P: %s" % game.current_pitcher,
                font=fonts['lastplay'], fill=colors['lastplay']))

        image = vertical_montage(fm)

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
    now_image = text_as_image(now.strftime(args.timestamp_format),
            font=fonts['timestamp'], fill=colors['timestamp'])

if args.vertical:
    montage = vertical_montage(images, 
            spacing=max(args.vpadding,0), halign='center', valign='center')
    if args.timestamp:
        montage = vertical_montage([montage, now_image],
                halign='center', valign='bottom')

    dir = os.path.dirname(args.vertical)
    if not os.path.exists(dir):
        os.makedirs(dir)

    montage.save(args.vertical)

if args.horizontal:
    montage = horizontal_montage(images,
            spacing=max(args.hpadding, 0), halign='center', valign='top')
    if args.timestamp:
        montage = horizontal_montage([now_image.rotate(90), montage],
                spacing=1, valign='center')

    dir = os.path.dirname(args.horizontal)
    if not os.path.exists(dir):
        os.makedirs(dir)

    montage.save(args.horizontal)
