#!/usr/bin/env python3
"""IRC bot for doing stupid stuff and sometimes handling commands for account creation."""
import argparse
import collections
import functools
import getpass
import os
import pkgutil
import re
import ssl
import threading
from configparser import ConfigParser
from textwrap import dedent
from traceback import format_exc
from types import FunctionType
from types import ModuleType
from typing import Any
from typing import Callable
from typing import DefaultDict
from typing import Dict
from typing import Match
from typing import NamedTuple
from typing import Pattern
from typing import Set

import irc.bot
import irc.connection
from irc.client import NickMask
from ocflib.misc.mail import send_problem_report

IRC_HOST = 'irc'
IRC_PORT = 6697

# TODO: set this value in the Dockerfile, instead of relying on this kludge
user = getpass.getuser()
TESTING = user != 'nobody'

if not TESTING:
    IRC_NICKNAME = 'create'
    IRC_CHANNELS_OPER = frozenset(('#rebuild', '#atool'))
    IRC_CHANNELS_ANNOUNCE = frozenset(('#atool',))
    IRC_CHANNELS_JOIN_MYSQL = True
else:
    IRC_NICKNAME = f'create-{user}'
    IRC_CHANNELS_OPER = IRC_CHANNELS_ANNOUNCE = frozenset(('#' + user,))
    IRC_CHANNELS_JOIN_MYSQL = False

NUM_RECENT_MESSAGES = 10

# 512 bytes is the max message length set by RFC 2812 on the max single message
# length, so messages need to split up into at least sections of that size,
# however clients (hexchat at least) appear to start cutting off less than that
# amount of text, so cut into small blocks to avoid that.
MAX_CLIENT_MSG = 435


class Listener(NamedTuple):
    pattern: Pattern
    fn: FunctionType
    help_text: str
    require_mention: bool
    require_oper: bool
    require_privileged_oper: bool

    @property
    def help(self) -> str:
        if self.help_text:
            return self.help_text
        else:
            return self.fn.__doc__ or ''

    @property
    def plugin_name(self) -> str:
        if isinstance(self.fn, functools.partial):
            return self.fn.func.__module__
        else:
            return self.fn.__module__


class MatchedMessage(NamedTuple):
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
    channel: str
    text: str
    raw_text: str
    match: Match
    is_oper: bool
    nick: str
    respond: Callable


class CreateBot(irc.bot.SingleServerIRCBot):

    def __init__(
            self,
            celery_conf,
            nickserv_password,
            rt_password,
            weather_apikey,
            mysql_password,
            googlesearch_key,
            googlesearch_cx,
            discourse_apikey,
            kanboard_apikey,
            twitter_apikeys,
    ):
        self.recent_messages: DefaultDict[str, Any] = collections.defaultdict(
            functools.partial(collections.deque, maxlen=NUM_RECENT_MESSAGES),
        )
        self.topics: Dict[str, str] = {}
        self.celery_conf = celery_conf
        self.tasks: Any = ()  # set in create plugin
        self.rt_password = rt_password
        self.nickserv_password = nickserv_password
        self.weather_apikey = weather_apikey
        self.mysql_password = mysql_password
        self.googlesearch_key = googlesearch_key
        self.googlesearch_cx = googlesearch_cx
        self.discourse_apikey = discourse_apikey
        self.kanboard_apikey = kanboard_apikey
        self.twitter_apikeys = twitter_apikeys
        self.listeners: Set[Listener] = set()
        self.plugins: Dict[str, ModuleType] = {}
        self.extra_channels: Set[str] = set()  # plugins can add stuff here

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

    def handle_error(self, error_message):
        # for debugging purposes
        print(error_message)

        # don't send emails when running as dev
        if not TESTING:
            send_problem_report(error_message)

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
        self.listeners.add(
            Listener(
                pattern=re.compile(pattern, flags),
                fn=fn,
                help_text=help_text,
                require_mention=require_mention,
                require_oper=require_oper,
                require_privileged_oper=require_privileged_oper,
            ),
        )

    def on_welcome(self, conn, _):
        conn.privmsg('NickServ', f'identify {self.nickserv_password}')

        # Join the "main" IRC channels.
        for channel in IRC_CHANNELS_OPER | IRC_CHANNELS_ANNOUNCE | self.extra_channels:
            conn.join(channel)

    def handle_chat(
            self,
            *,
            raw_text: str,
            user: str,
            channel: str,
            is_oper: bool,
            is_privileged_channel: bool,
            respond: Callable,
            pretend_mentioned: bool = False,
    ):
        was_mentioned = raw_text.lower().startswith((IRC_NICKNAME.lower() + ' ', IRC_NICKNAME.lower() + ': '))

        for listener in self.listeners:
            text = raw_text
            if listener.require_mention and not pretend_mentioned:
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
            if listener.require_privileged_oper and not is_privileged_channel:
                continue

            match = listener.pattern.search(text)
            if match is not None:
                msg = MatchedMessage(
                    channel=channel,
                    text=text,
                    raw_text=raw_text,
                    match=match,
                    is_oper=is_oper,
                    nick=user,
                    respond=respond,
                )
                try:
                    listener.fn(self, msg)
                except Exception as ex:
                    error_msg = 'ircbot exception in {module}/{function}: {exception}'.format(
                        module=listener.fn.__module__,
                        function=listener.fn.__name__,
                        exception=ex,
                    )
                    msg.respond(error_msg, ping=False)
                    self.handle_error(
                        dedent(
                            """
                        {error}

                        {traceback}

                        Message:
                            * Channel: {channel}
                            * Nick: {nick}
                            * Oper?: {oper}
                            * Text: {text}
                            * Raw text: {raw_text}
                            * Match groups: {groups}
                        """
                        ).format(
                            error=error_msg,
                            traceback=format_exc(),
                            channel=msg.channel,
                            nick=msg.nick,
                            oper=msg.is_oper,
                            text=msg.text,
                            raw_text=msg.raw_text,
                            groups=msg.match.groups(),
                        ),
                    )

        # everything gets logged except commands
        if raw_text[0] != '!':
            self.recent_messages[channel].appendleft((user, raw_text))

    def on_pubmsg(self, conn, event):
        if event.target in self.channels:
            user = NickMask(event.source).nick

            # Don't respond to other create bots to avoid loops
            if user.startswith('create'):
                return

            raw_text, = event.arguments

            def respond(raw_text, ping=True):
                fmt = '{user}: {raw_text}' if ping else '{raw_text}'
                full_raw_text = fmt.format(user=user, raw_text=raw_text)
                self.say(event.target, full_raw_text)

            self.handle_chat(
                raw_text=raw_text,
                user=user,
                channel=event.target,
                is_oper=user in self.channels[event.target].opers(),
                is_privileged_channel=event.target in IRC_CHANNELS_OPER,
                respond=respond,
            )

    def on_privmsg(self, conn, event):
        """Handle private (direct) messages.

        The name is misleading since PRIVMSG is also used for public (channel)
        messages in the IRC protocol. The library we use splits channel
        messages into a separate event, `on_pubmsg`.
        """
        raw_text, = event.arguments
        user = NickMask(event.source).nick

        def respond(raw_text, ping=False):
            # ping is ignored, since it makes little sense to ping somebody in a private message.
            self.say(user, raw_text)

        self.handle_chat(
            raw_text=raw_text,
            user=user,
            channel=user,
            is_oper=False,
            is_privileged_channel=False,
            respond=respond,
            pretend_mentioned=True,
        )

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

    def add_thread(self, func):
        def thread_func():
            try:
                func(self)
            except Exception as ex:
                error_msg = 'ircbot exception in thread {thread}.{function}: {exception}'.format(
                    thread=func.__module__,
                    function=func.__name__,
                    exception=ex,
                )
                self.say('#rebuild', error_msg)
                self.handle_error(
                    dedent(
                        """
                    {error}

                    {traceback}
                    """
                    ).format(
                        error=error_msg,
                        traceback=format_exc(),
                    ),
                )
            finally:
                # The thread has stopped, probably because it threw an error
                # This shouldn't happen, so we stop the entire bot
                os._exit(1)

        thread = threading.Thread(target=thread_func, daemon=True)
        thread.start()

    def bump_topic(self):
        for channel, topic in self.topics.items():
            def plusone(m):
                return '{}: {}'.format(m.group(1), int(m.group(2)) + 1)

            new_topic = re.sub(r'(days since.*?): (\d+)', plusone, topic)
            if topic != new_topic:
                self.connection.topic(channel, new_topic=new_topic)

    def say(self, channel, message):
        # Find the length of the full message
        msg_len = len(f'PRIVMSG {channel} :{message}\r\n'.encode('utf-8'))

        # The message must be split up if over the length limit
        if msg_len > MAX_CLIENT_MSG:
            messages = split_utf8(message.encode('utf-8'), MAX_CLIENT_MSG)

            for msg in messages:
                self.connection.privmsg(channel, msg)
        else:
            self.connection.privmsg(channel, message)


# Generator which splits the unicode message string
def split_utf8(s, n):
    while len(s) > n:
        k = n
        # All continuation bytes for utf-8 codepoints
        # are between 0x80 and 0xBF
        while (s[k] & 0xc0) == 0x80:
            k -= 1

        yield s[:k].decode('utf-8')
        s = s[k:]
    yield s.decode('utf-8')


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

    celery_conf = {
        'broker': conf.get('celery', 'broker'),
        'backend': conf.get('celery', 'backend'),
    }

    nickserv_password = conf.get('nickserv', 'password')
    rt_password = conf.get('rt', 'password')
    weather_apikey = conf.get('openweathermap', 'apikey')
    mysql_password = conf.get('mysql', 'password')
    googlesearch_key = conf.get('googlesearch', 'key')
    googlesearch_cx = conf.get('googlesearch', 'cx')
    discourse_apikey = conf.get('discourse', 'apikey')
    kanboard_apikey = conf.get('kanboard', 'apikey')
    twitter_apikeys = (
        conf.get('twitter', 'apikey'),
        conf.get('twitter', 'apisecret'),
    )

    bot = CreateBot(
        celery_conf, nickserv_password, rt_password,
        weather_apikey, mysql_password, googlesearch_key, googlesearch_cx,
        discourse_apikey, kanboard_apikey, twitter_apikeys,
    )

    # Start the bot!
    bot.start()


if __name__ == '__main__':
    main()
