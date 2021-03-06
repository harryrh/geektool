#!/opt/local/bin/python2.7
'''Get NFL Scores from ESPN'''

from BeautifulSoup import BeautifulSoup
from ConfigParser import SafeConfigParser
from PIL import Image, ImageFont, ImageFilter
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from datetime import date, time, datetime
from pytz import timezone
import os
import re
import sys
import urllib
from textwrap import fill, wrap

eastern = timezone('US/Eastern')

#-------------------------------------------------------------------------------

monthnum = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
        'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11,
        'December': 12 }


def one_of(*args):
    for i in args:
        if i:
            return i
    return None

def normalize(string):
    return re.subn('[^a-z0-9]', '', string.lower())[0]

class Team():
    
    def __init__(self, name, scores=None, record=None, game_record=None, winner=False, possession=None, image=None):

        self.name = name
        self.scores = scores
        self.record = record
        self.game_record = game_record
        self.winner = winner
        self.possession = possession
        self.image = image

    def __str__(self):

        info = []
        info.append('<Team')
        info.append('name=%s' % self.name)
        info.append('scores=%s' % ','.join(self.scores))
        info.append('record=%s' % self.record)
        info.append('game_record=%s' % self.game_record)
        info.append('possession=%s' % self.possession)
        info.append('winner=%s' % self.winner)
        info.append('image=%s' % self.image)
        info.append('>')

        return " ".join(info)

class Game():

    def __init__(self, away_team, home_team, type,
            status=None, tv=None, headline=None, date=None, lastplay=None, line=None):

        self.away_team = away_team
        self.home_team = home_team
        self.type = type
        self.status = status
        self.tv = tv
        self.headline = headline
        self.date = date
        self.lastplay = lastplay
        self.line = line

    def __str__(self):

        info = []
        info.append('<Game')
        info.append('away_team=%s' % self.away_team)
        info.append('home_team=%s' % self.home_team)
        info.append('type=%s' % self.type)
        info.append('date=%s' % self.date)
        info.append('status=%s' % self.status)
        info.append('tv=%s' % self.tv)
        info.append('headline=%s' % self.headline)
        info.append('lastplay=%s' % self.lastplay)
        info.append('line=%s' % self.line)
        info.append('>')

        return " ".join(info)

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

def render_game(game, fonts, colors):

    game_images = []

    away_image = game.away_team.image
    home_image = game.home_team.image

    upcoming = game.type.startswith('preview')

    if upcoming and game.away_team.record != 'N/A':
        ar = game.away_team.record.replace('-', ' - ')
        hr = game.home_team.record.replace('-', ' - ')
        ari = text_as_image(ar, font=fonts['record'], fill=colors['record'])
        hri = text_as_image(hr, font=fonts['record'], fill=colors['record'])
        away_image = vertical_montage([game.away_team.image, ari], halign='center')
        home_image = vertical_montage([game.home_team.image, hri], halign='center')

    icons = horizontal_montage([away_image, home_image], spacing=args.spacing)
    game_images.append(icons)

    if upcoming:
        delta = game.date - localtz.localize(datetime.now())
        game_images.append(text_as_image(game.date.strftime(args.date_format).upper(), font=fonts['date'], fill=colors['date']))
        if delta.days >= 7:
            game_images.append(text_as_image(game.date.strftime('%b %m, %Y'), font=fonts['date'], fill=colors['date']))

        if args.line and game.line:
            line_image = text_as_image(game.line, font=fonts['line'], fill=colors['line'])
            game_images.append(line_image)

        game_images.append(text_as_image(game.tv, font=fonts['tv'], fill=colors['tv']))

    else:
        if args.quarters:
            # Quarters as text
            (w, h) = icons.size

            asi = [text_as_image(s, font=fonts['quarter'], fill=colors['quarter']) for s in game.away_team.scores]
            hsi = [text_as_image(s, font=fonts['quarter'], fill=colors['quarter']) for s in game.home_team.scores]

            qis = []
            for x in zip(asi, hsi):
                qis.append(vertical_montage(list(x), halign='right', sameheight=True))
                
            quarters_image = horizontal_montage(qis, min_width=w/6, halign='right')

            game_images.append(quarters_image)
        else:
            # Summary score
            (iw, ih) = icons.size

            away_i = text_as_image("%s" % game.away_team.scores[5], font=fonts['score'], fill=colors['score'])
            home_i = text_as_image("%s" % game.home_team.scores[5], font=fonts['score'], fill=colors['score'])

            game_images.append(horizontal_montage([away_i, home_i], min_width=iw/2, halign='center', valign='center'))

        game_images.append(text_as_image(game.status.upper(), font=fonts['status'], fill=colors['status']))

        if args.headline and game.headline:
            hi = []
            for str in wrap(game.headline, 20):
                hi.append(text_as_image(str, font=fonts['headline'], fill=colors['headline']))
            game_images.append(vertical_montage(hi, halign='left'))

        if args.lastplay and game.lastplay:
            li = []
            for str in wrap(game.lastplay, 20):
                li.append(text_as_image(str, font=fonts['lastplay'], fill=colors['lastplay']))
            game_images.append(vertical_montage(li, halign='left'))

        if game.type == 'in-game':
            game_images.append(text_as_image(game.tv, font=fonts['tv'], fill=colors['tv']))

    return drop_shadow(vertical_montage(game_images, halign='center', spacing=0))


def render_games(games, fonts, fontcolor):
    game_images = []
    for game in games:
        game_images.append(render_game(game, fonts, colors))
    return game_images

#-------------------------------------------------------------------------------

conf_parser = ArgumentParser(add_help=False)
conf_parser.add_argument('-f', '--config-file', dest='config_file', metavar='FILE',
        help='Config file to load')
conf_parser.add_argument('-s', '--section',  dest='section', default='nfl',
        help='Section of Config File to use')
args, remaining_argv = conf_parser.parse_known_args()

parser = ArgumentParser(parents=[conf_parser],
        description=__doc__,
        formatter_class=ArgumentDefaultsHelpFormatter)

parser.add_argument('--font', dest='font', help='TrueType Font to Load')
parser.add_argument('--fontsize', dest='fontsize', type=int, help='Font Size')
parser.add_argument('--fontcolor', dest='fontcolor', default='white', help='Font Color (PIL)')
parser.add_argument('-d', '--date', dest='date', metavar='YYYYMMDD', help='Specific date')
parser.add_argument('--spacing', dest='spacing', type=int, help='Spacing between Logos')
parser.add_argument('--hpad', dest='hpadding', type=int, help='Horizontal Montage Spacing')
parser.add_argument('--vpad', dest='vpadding', type=int, help='Vertical Montage Spacing')
parser.add_argument('-V', '--vertical', dest='vertical', metavar='FILE', help='Vertical Montage File Name')
parser.add_argument('-H', '--horizontal', dest='horizontal', metavar='FILE', help='Horizontal Montage File Name')
parser.add_argument('-S', '--slideshow', dest='slideshow', help='Slideshow Directory')
parser.add_argument('-l', '--headline', dest='headline', action='store_true', help='Display headline')
parser.add_argument('--line', dest='line', action='store_true', help='Display line')
parser.add_argument('-q', '--quarters', dest='quarters', action='store_true', help='Display quarter scores')
parser.add_argument('--lastplay', dest='lastplay', action='store_true', help='Display last play summary')
parser.add_argument('-g', '--desaturate', dest='desaturate',
        default=False, action='store_true', help='Desaturate the image')
parser.add_argument('-L', '--libdir', dest='libdir', metavar='DIR', help='imageutils directory')
parser.add_argument('--timestamp', dest='timestamp', action='store_true', default=False,
        help='Add a timestamp to the image')
parser.add_argument('--timestamp-format', dest='timestamp_format', default='%m/%d %H:%M',
        help='Format for timestamp (strftime)')
parser.add_argument('--timezone', dest='timezone', default='US/Central', help='Local Time Zone')
parser.add_argument('--date-format', dest='date_format', default='%a %l:%M %p', metavar='FORMAT', help='Date format')
parser.add_argument('-T', '--type', dest='types', action='append', help='Filter to game types', choices=['in-game', 'preview', 'final-state'])

group = parser.add_mutually_exclusive_group()
group.add_argument('-n', '--next-week', dest='next_week', action='store_true', help='Next week')
group.add_argument('-p', '--previous-week', dest='prev_week', action='store_true', help='Previous week')
group.add_argument('-w', '--week', dest='week', type=int, help='Specify Week')

if args.config_file:
    config = SafeConfigParser()
    config.read(args.config_file)
    defaults = dict(config.items(args.section))
    parser.set_defaults(**defaults)

args = parser.parse_args()
vargs = vars(args)

try:
    localtz = timezone(args.timezone)
except:
    localtz = eastern

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
if args.libdir:
    sys.path.insert(0, args.libdir)
from imageutils import horizontal_montage, vertical_montage, text_as_image, drop_shadow

# 'http://scores.espn.go.com/nfl/scoreboard'

base_url = 'http://scores.espn.go.com/nfl/scoreboard'
html = urllib.urlopen(base_url).read()

this_week = BeautifulSoup(html).find('option', selected = 'selected')
(year, season, week) = [int(x.split('=')[1]) for x in this_week['value'][1:].split('&')]
print 'SEASON: %s, WEEK: %s' % (season, week)

# 'http://scores.espn.go.com/nfl/scoreboard?seasonYear=2011&seasonType=2&weekNumber=8'
# Get next week -- replace the html to be parsed
if args.next_week or args.prev_week or args.week:
    # <option value="?seasonYear=2011&amp;seasonType=2&amp;weekNumber=10" selected="selected">

    if args.next_week:
        week = int(week) + 1
    elif args.prev_week:
        week = int(week) - 1
    elif args.week:
        week = args.week

    p = { 'seasonYear': year, 'seasonType': season, 'weekNumber': week }
    url = '%s?%s' % (base_url, urllib.urlencode(p))

    html = urllib.urlopen(url).read()


container_re = re.compile('\d+-gameContainer')
soup = BeautifulSoup(html)

upcoming_re = re.compile('(\d+):(\d+) ([AP]M) ET')
date_re = re.compile('(\w+),\s+(\w+)\s+(\d+),\s+(\d+)')

def parse_team_block(block, blockid, ahprefix):

    name_b = block.find('p', 'team-name')
    try:
        name = name_b.a.text
    except AttributeError:
        name = name_b.text

    winner_b = block.find('div', id='%s-%sWinner' % (blockid, ahprefix))
    winner = winner_b['style'].endswith('display:block')

    possession_b = block.find('span', id='%s-%sPossession' % (blockid, ahprefix))
    possession = possession_b['style'].endswith('display:inline;')

    scores_b = block.find('ul', 'score')
    scores = tuple([li.text.replace('&nbsp;', '') for li in scores_b.findAll('li')])

    record_b = block.find('p', 'record')
    record_s = record_b.text
    try:
        (record, game_record) = record_s[1:-1].split(', ')
    except ValueError:
        (record, game_record) = ('N/A', 'N/A')


    return Team(name, winner=winner, possession=possession, scores=scores, record=record, game_record=game_record)

def get_image(team, args):
    return Image.open(args['image.' + normalize(team.name)])

games = []
dates = soup.findAll('h4', 'games-date')
for date_block in dates:
    dm = date_re.match(date_block.text)
    (gweekday, gmonth_name, gmonth_day, gyear) = dm.groups()
    game_date = date(int(gyear), monthnum[gmonth_name], int(gmonth_day))

    for c in date_block.nextSibling.contents:
        for game_block in c.findAll('div', id=container_re):
            blockid = game_block['id'].split('-')[0]
            type = game_block['class'].split(' ')[3]

            if args.types and type not in args.types:
                continue

            status_block = game_block.find('p', id='%s-statusText' % blockid)
            status = status_block.text.replace('&nbsp;', '').strip()

            headline = None
            lastplay = None
            tv = None
            line = None

            if type == 'preview':
                upcoming = upcoming_re.match(status)
                # Upcoming game -- parse the time into an actual time
                if upcoming:
                    hour = int(upcoming.group(1))
                    minute = int(upcoming.group(2))
                    ampm = upcoming.group(3)
                    if ampm == 'PM' and int(hour) < 12:
                        hour = hour + 12
                    game_time = time(int(hour), int(minute), tzinfo=eastern)
                    game_date = datetime.combine(game_date, game_time).astimezone(localtz)

                tv_block = game_block.find('div', id='%s-preTV' % blockid)
                tv = tv_block.p.text.replace('&nbsp;', '').strip()

                line_block = game_block.find('li', 'vegas-line')
                dailyline = line_block.find('a', href='dailylines')
                try:
                    line = "%s%s" % (dailyline.contents[1].text, dailyline.contents[2])
                except IndexError:
                    line = ''

            elif type == 'in-game':

                lastplay_block = game_block.find('div', id='%s-lastPlayText' % blockid)
                lastplay = lastplay_block.text.replace('&nbsp;', '')

                tv_block = game_block.find('div', id='%s-flagBar' % blockid)
                tv = tv_block.text.replace('&nbsp;', '').strip()
                    
                pass

            elif type == 'final-state':

                headline_block = game_block.find('div', id='%s-recapHeadline' % blockid)
                headline = headline_block.text.replace('&nbsp;', '').strip()

                pass


            away_block = game_block.find('div', 'team visitor')
            away_team = parse_team_block(away_block, blockid, 'a')
            away_team.image = get_image(away_team, vargs)

            home_block = game_block.find('div', 'team home')
            home_team = parse_team_block(home_block, blockid, 'h')
            home_team.image = get_image(home_team, vargs)

            print 'TYPE: ', type

            game = Game(away_team, home_team, type=type, status=status, tv=tv, headline=headline, date=game_date, lastplay=lastplay, line=line)

            games.append(game)

fonts = {}
try:
    fonts['default'] = ImageFont.truetype(args.font, args.fontsize)
except:
    fonts['default'] = ImageFont.load_default()

colors = {}
colors['default'] = args.fontcolor

for s in ('record', 'headline', 'date', 'quarter', 'tv', 'timestamp', 'week', 'lastplay', 'score', 'status', 'line'):
    fonts[s] = get_font(s, vargs, fonts['default'])
    colors[s] = get_color(s, vargs, colors['default'])

images = render_games(games, fonts, colors)

if args.slideshow:
    if not os.path.exists(args.slideshow):
        os.makedirs(args.slideshow)

    # Clean the directory -- sometimes there are fewer files
    for file in os.listdir(args.slideshow):
        os.remove(os.path.join(args.slideshow, file))
    
    # Save all the files
    for i, image in enumerate(images):
        filename = os.path.join(args.slideshow, 'nfl-game-%02d.png' % i)
        if args.desaturate:
            image = image.convert('LA')
        image.save(filename)


if season == 1:
    week_im = text_as_image("PRESEASON %d" % week, font=fonts['week'], fill=colors['week'])
elif season == 2:
    week_im = text_as_image("WEEK %d" % week, font=fonts['week'], fill=colors['week'])
elif season == 3:
    ptype = ['WILD CARD', 'DIVISIONAL', 'CONFERENCE', 'PRO BOWL', 'SUPER BOWL']
    week_im = text_as_image("%s" % ptype[week-1], font=fonts['week'], fill=colors['week'])

if args.timestamp:
    now = localtz.localize(datetime.now())
    now_image = text_as_image(now.strftime(args.timestamp_format), font=fonts['timestamp'], fill=colors['timestamp'])

if not images:
    images = [text_as_image('No Games', font=fonts['default'], fill=colors['default'])]

if args.vertical:
    montage = vertical_montage(images, spacing=max(int(args.vpad),0), halign='center')
    if args.timestamp:
        montage = vertical_montage([now_image, montage], halign='center')
    montage = vertical_montage([week_im, montage], halign='center')
    if args.desaturate:
        montage = montage.convert('LA')
    montage.save(args.vertical)

if args.horizontal:
    montage = horizontal_montage(images, spacing=max(int(args.hpad),0), valign='top')
    if args.timestamp:
        montage = horizontal_montage([now_image.rotate(90), montage], valign='center')
    montage = horizontal_montage([week_im.rotate(90), montage], valign='center')
    if args.desaturate:
        montage = montage.convert('LA')
    montage.save(args.horizontal)
