#!/usr/bin/env python3
"""IRC bot for doing stupid stuff and sometimes handling commmands for account creation."""
import argparse
import collections
import getpass
import random
import re
import ssl
import threading
import time
from configparser import ConfigParser
from datetime import date

import irc.bot
import irc.connection
import upsidedown
from celery import Celery
from celery import exceptions
from celery.events import EventReceiver
from irc.client import NickMask
from kombu import Connection
from ocflib.account.submission import AccountCreationCredentials
from ocflib.account.submission import get_tasks
from ocflib.infra.rt import rt_connection
from ocflib.infra.rt import RtTicket

from ircbot import debian_security
from ircbot import emoji
from ircbot import rackspace_monitoring
from ircbot import weather


IRC_HOST = 'irc'
IRC_PORT = 6697

IRC_CHANNELS = ('#rebuild', '#atool')
IRC_CHANNELS_ANNOUNCE = ('#atool',)

user = getpass.getuser()
if user == 'nobody':
    IRC_NICKNAME = 'create'
else:
    IRC_NICKNAME = 'create-{}'.format(user)
    IRC_CHANNELS = ('#' + user,)

NUM_RECENT_MESSAGES = 10

# Check for Debian security announcements every 5 minutes
DSA_FREQ = 5
# Print out Rackspace monitoring status every minute
MONITOR_FREQ = 1

# 512 bytes is the max message length set by RFC 2812 on the max single message
# length, so messages need to split up into at least sections of that size,
# however clients (hexchat at least) appear to start cutting off less than that
# amount of text, so cut into small blocks to avoid that.
MAX_CLIENT_MSG = 435


class CreateBot(irc.bot.SingleServerIRCBot):

    def __init__(self, tasks, nickserv_password, rt_password, rackspace_apikey, weather_apikey):
        self.recent_messages = collections.deque(maxlen=NUM_RECENT_MESSAGES)
        self.topics = {}
        self.tasks = tasks
        self.rt_password = rt_password
        self.nickserv_password = nickserv_password
        self.rackspace_apikey = rackspace_apikey
        self.weather_apikey = weather_apikey
        factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
        super().__init__(
            [(IRC_HOST, IRC_PORT)],
            IRC_NICKNAME,
            IRC_NICKNAME,
            connect_factory=factory
        )

    def on_welcome(self, conn, _):
        conn.privmsg('NickServ', 'identify {}'.format(self.nickserv_password))

        for channel in IRC_CHANNELS:
            conn.join(channel)

    def on_pubmsg(self, conn, event):
        is_oper = False

        if event.target in self.channels:
            # event.source is like 'ckuehl!~ckuehl@nitrogen.techxonline.net'
            assert event.source.count('!') == 1
            user = NickMask(event.source).nick

            # Don't respond to other create bots to avoid loops
            if user.startswith('create'):
                return

            if user in self.channels[event.target].opers():
                is_oper = True

            assert len(event.arguments) == 1
            msg = event.arguments[0]

            def respond(msg, ping=True):
                fmt = '{user}: {msg}' if ping else '{msg}'
                full_msg = fmt.format(user=user, msg=msg)
                self.say(event.target, full_msg)

            # maybe do something with it
            tickets = re.findall(r'(?:rt#|ocf.io/rt/)([0-9]+)', msg)
            replace = r'(?:^| )s([!@"#$%&\'*./:;=?\\^_`|~])(.+)\1(.*)\1g?$'
            replacement = re.search(replace, msg)
            shrug = re.search(r's+h+r+(u+)g+', msg)
            sux = re.match(r'!sux (.+)$', msg)
            if tickets:
                rt = rt_connection(user='create', password=self.rt_password)
                for ticket in tickets:
                    try:
                        t = RtTicket.from_number(rt, int(ticket))
                        respond(str(t))
                    except AssertionError:
                        pass
            elif shrug:
                width = len(shrug.group(1))
                respond('¯\\' + ('_' * width) + '(ツ)' + ('_' * width) + '/¯', ping=False)
            elif msg.startswith((IRC_NICKNAME + ' ', IRC_NICKNAME + ': ')):
                command, *args = msg[len(IRC_NICKNAME) + 1:].strip().split(' ')
                self.handle_command(is_oper, command.lower(), args, respond)
            elif replacement:
                old = replacement.group(2)

                # By default, re.sub processes strings like r'\n' for escapes,
                # turning it into an actual newline. By using a function for
                # the replacement, we avoid the parsing of escape sequences.
                # https://github.com/ocf/ircbot/issues/3
                def new(_):
                    return '\x02{}\x02'.format(replacement.group(3))

                for user, msg in self.recent_messages:
                    try:
                        new_msg = re.sub(old, new, msg)
                        if new_msg != msg:
                            respond('<{}> {}'.format(user, new_msg), ping=False)
                            break
                    except re.error:
                        continue
            elif msg == '!flip':
                respond('my quantum randomness says: {}'.format(
                    random.choice(('approve', 'reject')),
                ))
            elif sux:
                respond(
                    'fuck {0}; {0} sucks; {0} is dying; {0} is dead to me; {0} hit wtc'.format(sux.group(1)),
                    ping=False,
                )

            # everything gets logged
            self.recent_messages.appendleft((user, msg))

    def handle_command(self, is_oper, command, args, respond):
        if is_oper:
            if command == 'list':
                task = self.tasks.get_pending_requests.delay()
                try:
                    task.wait(timeout=5)
                    if task.result:
                        for request in task.result:
                            respond(request)
                    else:
                        respond('no pending requests')
                except exceptions.TimeoutError:
                    respond('timed out loading list of requests, sorry!')
            elif command == 'approve':
                user_name = args[0]
                self.tasks.approve_request.delay(user_name)
                respond('approved {}, the account is being created'.format(user_name))
            elif command == 'reject':
                user_name = args[0]
                self.tasks.reject_request.delay(user_name)
                respond('rejected {}, better luck next time'.format(user_name))

            if command == 'newday':
                self.bump_topic()

            if command == 'status':
                respond(rackspace_monitoring.get_summary(self.rackspace_apikey))

        if command.startswith('thanks'):
            respond(random.choice((
                "you're welcome",
                'you are most welcome',
                'any time',
                'sure thing boss',
            )))
        elif command == 'thank':
            thing = ' '.join(args)
            if thing.lower().startswith('you'):
                respond("you're most welcome")
            else:
                respond('thanks, {}!'.format(thing), ping=False)

        if command in {'ban', 'flip', 'sorry'}:
            respond('(╯°□°）╯︵ ┻━┻ {}'.format(
                upsidedown.transform(' '.join(args)),
            ))

        if command in {'emoji', 'remoji'}:
            getattr(emoji, command)(respond, ' '.join(args))

        if command in {'weather', 'cold', 'hot'}:
            where = ' '.join(args) or 'Berkeley, CA'
            location = weather.find_match(where)
            summary = None
            if location:
                summary = weather.get_summary(self.weather_apikey, location)
            if summary:
                respond(summary, ping=False)
            else:
                respond('idk where {} is'.format(where))

    def on_currenttopic(self, connection, event):
        channel, topic = event.arguments
        self.topics[channel] = topic

    def on_topic(self, connection, event):
        topic, = event.arguments
        self.topics[event.target] = topic

    def bump_topic(self):
        for channel, topic in self.topics.items():
            def plusone(m):
                return '{}: {}'.format(m.group(1), int(m.group(2)) + 1)

            new_topic = re.sub('(days since.*?): (\d+)', plusone, topic)
            if topic != new_topic:
                self.connection.topic(channel, new_topic=new_topic)

    def say(self, channel, message):
        # Find the length of the full message
        msg_len = len('PRIVMSG {} :{}\r\n'.format(channel, message).encode('utf-8'))

        # The message must be split up if over the length limit
        if msg_len > MAX_CLIENT_MSG:
            # Split up the full message into chunks to send
            msg_range = range(0, len(message), MAX_CLIENT_MSG)
            messages = [message[i:i + MAX_CLIENT_MSG] for i in msg_range]

            for msg in messages:
                self.connection.privmsg(channel, msg)
        else:
            self.connection.privmsg(channel, message)


def bot_announce(bot, targets, message):
    for target in targets:
        bot.say(target, message)


def celery_listener(bot, celery, uri):
    """Listen for events from Celery, relay to IRC."""
    connection = Connection(uri, ssl={
        'ssl_ca_certs': '/etc/ssl/certs/ca-certificates.crt',
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
    })

    def on_account_created(event):
        request = event['request']
        bot_announce(
            bot,
            IRC_CHANNELS_ANNOUNCE,
            '{user} created ({real_name})'.format(
                user=request['user_name'],
                real_name=request['real_name'],
            ),
        )

    def on_account_submitted(event):
        request = event['request']
        bot_announce(
            bot,
            IRC_CHANNELS,
            '{user} ({real_name}) needs approval: {reasons}'.format(
                user=request['user_name'],
                real_name=request['real_name'],
                reasons=', '.join(request['reasons']),
            ),
        )

    def on_account_approved(event):
        request = event['request']
        bot_announce(
            bot,
            IRC_CHANNELS_ANNOUNCE,
            '{user} was approved, now pending creation.'.format(
                user=request['user_name'],
            ),
        )

    def on_account_rejected(event):
        request = event['request']
        bot_announce(
            bot,
            IRC_CHANNELS_ANNOUNCE,
            '{user} was rejected.'.format(
                user=request['user_name'],
            ),
        )

    while True:
        with connection as conn:
            recv = EventReceiver(
                conn,
                app=celery,
                handlers={
                    'ocflib.account_created': on_account_created,
                    'ocflib.account_submitted': on_account_submitted,
                    'ocflib.account_approved': on_account_approved,
                    'ocflib.account_rejected': on_account_rejected,
                },
            )
            recv.capture(limit=None, timeout=None)


def timer(bot):
    last_date = None
    last_dsa_check = None
    last_monitor_check = None
    last_monitor_status = None

    while not bot.connection.connected:
        time.sleep(2)

    while True:
        last_date, old = date.today(), last_date
        if old and last_date != old:
            bot.bump_topic()

        if last_dsa_check is None or time.time() - last_dsa_check > 60 * DSA_FREQ:
            last_dsa_check = time.time()

            for line in debian_security.get_new_dsas():
                bot.say('#rebuild', line)

        if last_monitor_check is None or time.time() - last_monitor_check > 60 * MONITOR_FREQ:
            last_monitor_check = time.time()
            new_monitor_status = rackspace_monitoring.get_summary(bot.rackspace_apikey)

            # Only print out Rackspace status if it has changed since the last check
            if last_monitor_status and last_monitor_status != new_monitor_status:
                bot.say('#rebuild', new_monitor_status)

            last_monitor_status = new_monitor_status

        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(
        description='OCF account creation IRC bot',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '-c',
        '--config',
        default='/etc/ocf-ircbot/ocf-ircbot.conf',
        help='Config file to read from.',
    )
    args = parser.parse_args()

    conf = ConfigParser()
    conf.read(args.config)

    celery = Celery(
        broker=conf.get('celery', 'broker'),
        backend=conf.get('celery', 'backend'),
    )
    celery.conf.broker_use_ssl = {
        'ssl_ca_certs': '/etc/ssl/certs/ca-certificates.crt',
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
    }
    # `redis_backend_use_ssl` is an OCF patch which was proposed upstream:
    # https://github.com/celery/celery/pull/3831
    celery.conf.redis_backend_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE,
    }

    # TODO: stop using pickle
    celery.conf.task_serializer = 'pickle'
    celery.conf.result_serializer = 'pickle'
    celery.conf.accept_content = {'pickle'}

    creds = AccountCreationCredentials(**{
        field:
            conf.get(*field.split('_'))
            for field in AccountCreationCredentials._fields
    })
    tasks = get_tasks(celery, credentials=creds)

    rt_password = conf.get('rt', 'password')
    nickserv_password = conf.get('nickserv', 'password')
    rackspace_apikey = conf.get('rackspace', 'apikey')
    weather_apikey = conf.get('weather_underground', 'apikey')

    # irc bot thread
    bot = CreateBot(tasks, nickserv_password, rt_password, rackspace_apikey, weather_apikey)
    bot_thread = threading.Thread(target=bot.start, daemon=True)
    bot_thread.start()

    # celery thread
    celery_thread = threading.Thread(
        target=celery_listener,
        args=(bot, celery, conf.get('celery', 'broker')),
        daemon=True,
    )
    celery_thread.start()

    # timer thread
    timer_thread = threading.Thread(
        target=timer,
        args=(bot,),
        daemon=True,
    )
    timer_thread.start()

    while True:
        for thread in (bot_thread, celery_thread, timer_thread):
            if not thread.is_alive():
                raise RuntimeError('Thread exited: {}'.format(thread))

        time.sleep(0.1)


if __name__ == '__main__':
    main()
