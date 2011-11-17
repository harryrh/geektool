#!/opt/local/bin/python2.7
'''Get NFL Scores from ESPN'''

from BeautifulSoup import BeautifulSoup
from ConfigParser import SafeConfigParser
from PIL import Image, ImageFont
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from datetime import date, time, datetime
from pytz import timezone
import os
import re
import sys
import urllib

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
    
    def __init__(self, name, score=None, record=None, image=None):

        self.name = name
        self.score = score
        self.record = record
        self.image = image

    def __repr__(self):

        info = []
        info.append('<Team')
        info.append('name="%s"' % self.name)
        info.append('score="%s"' % self.score)
        info.append('record="%s"' % self.record)
        info.append('image="%s"' % self.image)

        return " ".join(info)

class Game():

    def __init__(self, away_team, home_team,
            status=None, tv=None, headline=None, date=None):

        self.away_team = away_team
        self.home_team = home_team
        self.status = status
        self.tv = tv
        self.headline = headline
        self.date = date

    def __repr__(self):

        info = []
        info.append('<Game')
        info.append('away_team="%s"' % self.away_team)
        info.append('home_team="%s"' % self.home_team)
        info.append('status="%s"' % self.status)
        info.append('tv="%s"' % self.tv)
        info.append('headline="%s"' % self.headline)
        info.append('>')

        return " ".join(info)

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

if args.config_file:
    config = SafeConfigParser()
    config.read(args.config_file)
    defaults = dict(config.items(args.section))
    parser.set_defaults(**defaults)

parser.add_argument('--font', dest='font', help='TrueType Font to Load')
parser.add_argument('--fontsize', dest='fontsize', type=int, help='Font Size')
parser.add_argument('--fontcolor', dest='fontcolor', help='Font Color (PIL)')
parser.add_argument('-d', '--date', dest='date', metavar='YYYYMMDD', help='Specific date')
parser.add_argument('--spacing', dest='spacing', type=int, help='Spacing between Logos')
parser.add_argument('--hpad', dest='hpadding', type=int, help='Horizontal Montage Spacing')
parser.add_argument('--vpad', dest='vpadding', type=int, help='Vertical Montage Spacing')
parser.add_argument('-V', '--vertical', dest='vertical', metavar='FILE', help='Vertical Montage File Name')
parser.add_argument('-H', '--horizontal', dest='horizontal', metavar='FILE', help='Horizontal Montage File Name')
parser.add_argument('-S', '--slideshow', dest='slideshow', help='Slideshow Directory')
parser.add_argument('-l', '--headline', dest='headline', action='store_true', help='Display headline')
parser.add_argument('-q', '--quarters', dest='quarters', action='store_true', help='Display quarter scores')
parser.add_argument('-g', '--desaturate', dest='desaturate',
        default=False, action='store_true', help='Desaturate the image')
parser.add_argument('-L', '--libdir', dest='libdir', metavar='DIR', help='imageutils directory')
parser.add_argument('--adjust-time', dest='adjust_time', type=int, help='Adjust Gametime by hours')

group = parser.add_mutually_exclusive_group()
group.add_argument('-n', '--next-week', dest='next_week', action='store_true', help='Next week')
group.add_argument('-p', '--previous-week', dest='prev_week', action='store_true', help='Previous week')
group.add_argument('-w', '--week', dest='week', type=int, help='Specify Week')

args = parser.parse_args()
vargs = vars(args)

try:
    localtz = timezone(args.tz)
except:
    localtz = eastern

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
if args.libdir:
    sys.path.insert(0, args.libdir)
from imageutils import horizontal_montage, vertical_montage, text_as_image

# 'http://scores.espn.go.com/nfl/scoreboard'

base_url = 'http://scores.espn.go.com/nfl/scoreboard'
html = urllib.urlopen(base_url).read()

this_week = BeautifulSoup(html).find('option', selected = 'selected')
(year, season, week) = [x.split('=')[1] for x in this_week['value'][1:].split('&')]

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

def parse_team_block(block):

    name = block.contents[2].contents[0].a.text
    record = block.contents[2].contents[1].text

    score_block = block.find('ul', attrs = { 'class': 'score' })
    score = [s.text.replace('&nbsp;', '') for s in score_block.contents]

    image = Image.open(vargs['image.' + normalize(name)]).convert('RGBA')

    return Team(name, score=score, record=record, image=image)

upcoming_re = re.compile('(\d+):(\d+) ([AP]M) ET')
date_re = re.compile('(\w+),\s+(\w+)\s+(\d+),\s+(\d+)')

games = []
dates = soup.findAll('h4', 'games-date')
for i, d in enumerate(dates):
    dm = date_re.match(d.text)
    (gweekday, gmonth_name, gmonth_day, gyear) = dm.groups()
    game_date = date(int(gyear), monthnum[gmonth_name], int(gmonth_day))
    for j, c in enumerate(d.nextSibling.contents):
        for i, g in enumerate(c.findAll('div', id=container_re)):
            status_block = g.find('div', attrs = { 'class': 'game-status' })
            status = status_block.p.text.replace('&nbsp;', '').strip()

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

            tv_block = g.find('div', attrs = { 'class': 'tv' })
            tv = tv_block.p.text.replace('&nbsp;', '').strip()

            headline_block = g.find('div', attrs = { 'class': 'headline' })
            headline = headline_block.text.replace('&nbsp;', '').strip()

            away_block = g.find('div', attrs = { 'class': 'team visitor' })
            away_team = parse_team_block(away_block)

            home_block = g.find('div', attrs = { 'class': 'team home' })
            home_team = parse_team_block(home_block)

            game = Game(away_team, home_team, status=status, tv=tv, headline=headline, date=game_date)

            games.append(game)


try:
    font = ImageFont.truetype(args.font, args.fontsize)
except:
    font = ImageFont.load_default()

try:
    record_font = ImageFont.truetype(vargs['record.font'], int(vargs['record.fontsize']))
except:
    record_font = font

try:
    headline_font = ImageFont.truetype(vargs['headline.font'], int(vargs['headline.fontsize']))
except:
    headline_font = font

try:
    date_font = ImageFont.truetype(vargs['date.font'], int(vargs['date.fontsize']))
except:
    date_font = font

try:
    quarter_font = ImageFont.truetype(vargs['quarter.font'], int(vargs['quarter.fontsize']))
except:
    quarter_font = font

try:
    tv_font = ImageFont.truetype(vargs['tv.font'], int(vargs['tv.fontsize']))
except:
    tv_font = font

fontcolor = 'white'
if args.fontcolor:
    fontcolor=args.fontcolor

images = []
for g in games:
    gi = []

    upcoming = upcoming_re.match(g.status)

    away_image = g.away_team.image
    home_image = g.home_team.image
    if upcoming:
        ar = g.away_team.record[1:g.away_team.record.find(',')]
        hr = g.home_team.record[1:g.home_team.record.find(',')]
        ari = text_as_image(ar, font=record_font, fill=fontcolor)
        hri = text_as_image(hr, font=record_font, fill=fontcolor)
        away_image = vertical_montage([g.away_team.image, ari], halign='center')
        home_image = vertical_montage([g.home_team.image, hri], halign='center')

    icons = horizontal_montage([away_image, home_image], spacing=args.spacing)
    gi.append(icons)


    if upcoming:
        delta = g.date - datetime.now().replace(tzinfo=localtz)
        gi.append(text_as_image(g.date.strftime('%a %l:%M %p %Z'), font=date_font, fill=fontcolor))
        if delta.days >= 7:
            gi.append(text_as_image(g.date.strftime('%b %m, %Y'), font=date_font, fill=fontcolor))
        gi.append(text_as_image(g.tv, font=tv_font, fill=fontcolor))
    else:
        if args.quarters:
            # Quarters as text
            (w, h) = icons.size

            asi = [text_as_image(s, font=quarter_font, fill=fontcolor) for s in g.away_team.score]
            hsi = [text_as_image(s, font=quarter_font, fill=fontcolor) for s in g.home_team.score]

            qis = []
            for x in zip(asi, hsi):
                qis.append(vertical_montage(list(x), halign='right', sameheight=True))
                
            quarters_image = horizontal_montage(qis, min_width=w/6, halign='right')

            gi.append(quarters_image)
        else:
            # Summary score
            gi.append(text_as_image("%s - %s" % (g.away_team.score[5], g.home_team.score[5]),
                font=font, fill=fontcolor))
        gi.append(text_as_image(g.status, font=font, fill=fontcolor))
        if g.headline and args.headline:
            gi.append(text_as_image(g.headline, font=headline_font, fill=fontcolor))

    image = vertical_montage(gi, halign='center', spacing=0)

    images.append(image)


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

week_im = text_as_image("WEEK %s" % week, font=font, fill=fontcolor)

if not images:
    images = [text_as_image('No Games', font=font, fill=fontcolor)]

if args.vertical:
    montage = vertical_montage(images, spacing=max(int(args.vpad),0), halign='center')
    montage = vertical_montage([week_im, montage], halign='center')
    if args.desaturate:
        montage = montage.convert('LA')
    montage.save(args.vertical)

if args.horizontal:
    montage = horizontal_montage(images, spacing=max(int(args.hpad),0), valign='top')
    montage = horizontal_montage([week_im.rotate(90), montage], valign='center')
    if args.desaturate:
        montage = montage.convert('LA')
    montage.save(args.horizontal)
