#!/usr/bin/env python3
"""IRC bot for doing stupid stuff and sometimes handling commands for account creation."""
import argparse
import collections
import functools
import getpass
import pkgutil
import re
import ssl
import threading
import time
from configparser import ConfigParser
from datetime import date

import irc.bot
import irc.connection
from celery import Celery
from irc.client import NickMask
from ocflib.account.submission import AccountCreationCredentials
from ocflib.account.submission import get_tasks

from ircbot.plugin import create
from ircbot.plugin import debian_security
from ircbot.plugin import rackspace_monitoring

IRC_HOST = 'irc'
IRC_PORT = 6697

user = getpass.getuser()
if user == 'nobody':
    IRC_NICKNAME = 'create'
    IRC_CHANNELS_OPER = frozenset(('#rebuild', '#atool'))
    IRC_CHANNELS_ANNOUNCE = frozenset(('#atool',))
    IRC_CHANNELS_JOIN_MYSQL = True
else:
    IRC_NICKNAME = 'create-{}'.format(user)
    IRC_CHANNELS_OPER = IRC_CHANNELS_ANNOUNCE = frozenset(('#' + user,))
    IRC_CHANNELS_JOIN_MYSQL = False

NUM_RECENT_MESSAGES = 10

# Check for Debian security announcements every 5 minutes
DSA_FREQ = 5
# Print out Rackspace monitoring status at most every minute
MONITOR_FREQ = 1

# 512 bytes is the max message length set by RFC 2812 on the max single message
# length, so messages need to split up into at least sections of that size,
# however clients (hexchat at least) appear to start cutting off less than that
# amount of text, so cut into small blocks to avoid that.
MAX_CLIENT_MSG = 435


class Listener(collections.namedtuple(
    'Listener',
    ('pattern', 'fn', 'help_text', 'require_mention', 'require_oper', 'require_privileged_oper'),
)):

    __slots__ = ()

    @property
    def help(self):
        if self.help_text:
            return self.help_text
        else:
            return self.fn.__doc__

    @property
    def plugin_name(self):
        if isinstance(self.fn, functools.partial):
            return self.fn.func.__module__
        else:
            return self.fn.__module__


class MatchedMessage(collections.namedtuple(
    'MatchedMessage',
    ('channel', 'text', 'raw_text', 'match', 'is_oper', 'nick', 'respond'),
)):
    """A message matching a listener.

    :param channel: IRC channel (as a string).
    :param text: The message text after processing. Processing includes
                 chopping off the bot nickname from the front.
    :param raw_text: The raw, unparsed text. Usually "text" is more useful.
    :param match: The regex match object.
    :param is_oper: Whether the user is an operator.
    :param nick: The nickname of the user.
    :param respond: A function to respond to this message in the correct
                    channel and pinging the correct person.
    """

    __slots__ = ()


class CreateBot(irc.bot.SingleServerIRCBot):

    def __init__(
            self,
            tasks,
            nickserv_password,
            rt_password,
            rackspace_apikey,
            weather_apikey,
            mysql_password,
            marathon_creds,
            googlesearch_key,
            googlesearch_cx,
            discourse_apikey,
            twitter_apikeys,
    ):
        self.recent_messages = collections.defaultdict(
            functools.partial(collections.deque, maxlen=NUM_RECENT_MESSAGES),
        )
        self.topics = {}
        self.tasks = tasks
        self.rt_password = rt_password
        self.nickserv_password = nickserv_password
        self.rackspace_apikey = rackspace_apikey
        self.weather_apikey = weather_apikey
        self.mysql_password = mysql_password
        self.marathon_creds = marathon_creds
        self.googlesearch_key = googlesearch_key
        self.googlesearch_cx = googlesearch_cx
        self.discourse_apikey = discourse_apikey
        self.twitter_apikeys = twitter_apikeys
        self.listeners = set()
        self.plugins = {}
        self.extra_channels = set()  # plugins can add stuff here

        # Register plugins before joining the server.
        self.register_plugins()

        factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
        super().__init__(
            [(IRC_HOST, IRC_PORT)],
            IRC_NICKNAME,
            IRC_NICKNAME,
            connect_factory=factory,
        )

    def register_plugins(self):
        for importer, mod_name, _ in pkgutil.iter_modules(['ircbot/plugin']):
            mod = importer.find_module(mod_name).load_module(mod_name)
            self.plugins[mod_name] = mod
            register = getattr(mod, 'register', None)
            if register is not None:
                register(self)

    def listen(
            self,
            pattern,
            fn,
            flags=0,
            help_text=None,
            require_mention=False,
            require_oper=False,
            require_privileged_oper=False,
    ):
        self.listeners.add(Listener(
            pattern=re.compile(pattern, flags),
            fn=fn,
            help_text=help_text,
            require_mention=require_mention,
            require_oper=require_oper,
            require_privileged_oper=require_privileged_oper,
        ))

    def on_welcome(self, conn, _):
        conn.privmsg('NickServ', 'identify {}'.format(self.nickserv_password))

        # Join the "main" IRC channels.
        for channel in IRC_CHANNELS_OPER | IRC_CHANNELS_ANNOUNCE | self.extra_channels:
            conn.join(channel)

    def on_pubmsg(self, conn, event):
        if event.target in self.channels:
            is_oper = False
            # event.source is like 'ckuehl!~ckuehl@raziel.ckuehl.me'
            assert event.source.count('!') == 1
            user = NickMask(event.source).nick

            # Don't respond to other create bots to avoid loops
            if user.startswith('create'):
                return

            if user in self.channels[event.target].opers():
                is_oper = True

            assert len(event.arguments) == 1
            raw_text = event.arguments[0]

            def respond(raw_text, ping=True):
                fmt = '{user}: {raw_text}' if ping else '{raw_text}'
                full_raw_text = fmt.format(user=user, raw_text=raw_text)
                self.say(event.target, full_raw_text)

            was_mentioned = raw_text.startswith((IRC_NICKNAME + ' ', IRC_NICKNAME + ': '))

            for listener in self.listeners:
                text = raw_text
                if listener.require_mention:
                    if was_mentioned:
                        # Chop off the bot nickname.
                        text = text.split(' ', 1)[1]
                    else:
                        continue

                if (
                    (listener.require_oper or listener.require_privileged_oper) and
                    not is_oper
                ):
                    continue

                # Prevent people from creating a channel, becoming oper,
                # inviting the bot, and approving/rejecting accounts without
                # "real" oper privilege.
                if listener.require_privileged_oper and event.target not in IRC_CHANNELS_OPER:
                    continue

                match = listener.pattern.search(text)
                if match is not None:
                    msg = MatchedMessage(
                        channel=event.target,
                        text=text,
                        raw_text=raw_text,
                        match=match,
                        is_oper=is_oper,
                        nick=user,
                        respond=respond,
                    )
                    listener.fn(self, msg)

            # everything gets logged except commands
            if raw_text[0] != '!':
                self.recent_messages[event.target].appendleft((user, raw_text))

    def on_currenttopic(self, connection, event):
        channel, topic = event.arguments
        self.topics[channel] = topic

    def on_topic(self, connection, event):
        topic, = event.arguments
        self.topics[event.target] = topic

    def on_invite(self, connection, event):
        # TODO: make this more plugin-like
        import ircbot.plugin.channels
        return ircbot.plugin.channels.on_invite(self, connection, event)

    def bump_topic(self):
        for channel, topic in self.topics.items():
            def plusone(m):
                return '{}: {}'.format(m.group(1), int(m.group(2)) + 1)

            new_topic = re.sub(r'(days since.*?): (\d+)', plusone, topic)
            if topic != new_topic:
                self.connection.topic(channel, new_topic=new_topic)

    def say(self, channel, message):
        # Find the length of the full message
        msg_len = len('PRIVMSG {} :{}\r\n'.format(channel, message).encode('utf-8'))

        # The message must be split up if over the length limit
        if msg_len > MAX_CLIENT_MSG:
            messages = self.split_utf8(message.encode('utf-8'), MAX_CLIENT_MSG)

            for msg in messages:
                self.connection.privmsg(channel, msg)
        else:
            self.connection.privmsg(channel, message)

    # Generator which splits the unicode message string
    def split_utf8(self, s, n):
        while len(s) > n:
            k = n
            # All continuation bytes for utf-8 codepoints
            # are between 0x80 and 0xBF
            while (s[k] & 0xc0) == 0x80:
                k -= 1

            yield s[:k].decode('utf-8')
            s = s[k:]
        yield s.decode('utf-8')


def timer(bot):
    last_date = None
    last_dsa_check = None
    last_monitor_check = None
    last_monitor_status = None

    while not bot.connection.connected:
        time.sleep(2)

    # TODO: timers should register as plugins like listeners do
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
            try:
                new_monitor_status = rackspace_monitoring.get_summary(bot.rackspace_apikey)
            except Exception as ex:
                new_monitor_status = 'Error getting status: {}'.format(ex)

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
    mysql_password = conf.get('mysql', 'password')
    marathon_creds = (
        conf.get('marathon', 'user'),
        conf.get('marathon', 'password'),
    )
    googlesearch_key = conf.get('googlesearch', 'key')
    googlesearch_cx = conf.get('googlesearch', 'cx')
    discourse_apikey = conf.get('discourse', 'apikey')
    twitter_apikeys = (
        conf.get('twitter', 'apikey'),
        conf.get('twitter', 'apisecret'),
    )

    # irc bot thread
    bot = CreateBot(
        tasks, nickserv_password, rt_password, rackspace_apikey,
        weather_apikey, mysql_password, marathon_creds,
        googlesearch_key, googlesearch_cx, discourse_apikey,
        twitter_apikeys,
    )
    bot_thread = threading.Thread(target=bot.start, daemon=True)
    bot_thread.start()

    # celery thread
    celery_thread = threading.Thread(
        target=create.celery_listener,
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
