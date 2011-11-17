#!/opt/local/bin/python2.7

import imaplib
import email
import sys
import re
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

parser = ArgumentParser(description=__doc__,
        formatter_class=ArgumentDefaultsHelpFormatter)

parser.add_argument('-s', '--search', dest='search', default='RECENT', choices=['ALL', 'RECENT'])
parser.add_argument('-p', '--port', dest='port', type=int, default=993)
parser.add_argument('-m', '--mailbox', dest='mailbox', default='INBOX')
parser.add_argument('host', help='Host, e.g. imap.gmail.com, mail.me.com')
parser.add_argument('user')
parser.add_argument('password')
args = parser.parse_args()

flag_re = re.compile('\\\\([A-Z][a-z]+)')

imapcon = imaplib.IMAP4_SSL(args.host, args.port)
rc, resp = imapcon.login(args.user, args.password)
message_count = imapcon.select(args.mailbox, True)
t, d = imapcon.search(None, args.search)
try:
    if len(d[0]):
        messages = d[0].split(" ")
        for id in reversed(messages[-5:]):
            t, data = imapcon.fetch(id, '(FLAGS RFC822)')
            msg = email.message_from_string(data[0][1])
            flags = flag_re.findall(data[1])
            print "%s | %s | %s (%s)" % (
                    msg['Subject'], msg['From'], msg['Date'], " ".join(flags))
    else:
        print 'No messages'
except:
    pass

imapcon.logout()
