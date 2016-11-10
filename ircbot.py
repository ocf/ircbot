#!/usr/bin/env python3
"""IRC bot for printing info and handling commmands for account creation."""
import argparse
import getpass
import re
import ssl
import threading
import time
from configparser import ConfigParser
from datetime import date

import irc.bot
import irc.connection
from celery import Celery
from celery import exceptions
from celery.events import EventReceiver
from kombu import Connection
from ocflib.account.submission import AccountCreationCredentials
from ocflib.account.submission import get_tasks
from ocflib.infra.rt import rt_connection
from ocflib.infra.rt import RtTicket


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


class CreateBot(irc.bot.SingleServerIRCBot):

    def __init__(self, tasks, nickserv_password, rt_password):
        self.recent_messages = []
        self.topics = {}
        self.tasks = tasks
        self.rt_password = rt_password
        self.nickserv_password = nickserv_password
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
            # TODO: irc library provides a nice way to parse these
            # event.source is like 'ckuehl!~ckuehl@nitrogen.techxonline.net'
            assert event.source.count('!') == 1
            user, _ = event.source.split('!')

            if user.startswith('create'):
                return

            if user in self.channels[event.target].opers():
                is_oper = True

            assert len(event.arguments) == 1
            msg = event.arguments[0]

            def respond(msg, ping=True):
                fmt = '{user}: {msg}' if ping else '{msg}'
                conn.privmsg(event.target, fmt.format(user=user, msg=msg))

            # maybe do something with it
            tickets = re.findall(r'rt#([0-9]+)', msg)
            replacement = re.search(r's(.)(.+)\1(.*)\1', msg)
            if tickets:
                rt = rt_connection(user='create', password=self.rt_password)
                for ticket in tickets:
                    try:
                        t = RtTicket.from_number(rt, int(ticket))
                        respond(str(t))
                    except AssertionError:
                        pass
            elif msg.startswith((IRC_NICKNAME + ' ', IRC_NICKNAME + ': ')):
                command, *args = msg[len(IRC_NICKNAME) + 1:].strip().split(' ')
                self.handle_command(is_oper, command, args, respond)
            elif replacement:
                old = replacement.group(2)
                new = '\x02{}\x02'.format(replacement.group(3))
                for user, msg in self.recent_messages[::-1]:
                    new_msg = re.sub(old, new, msg)
                    if new_msg != msg:
                        respond('<{}> {}'.format(user, new_msg), ping=False)
                        break

            # everything gets logged
            self.recent_messages.append((user, msg))
            while len(self.recent_messages) > 10:
                self.recent_messages.pop(0)

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

        if command == 'thanks':
            respond('you\'re welcome')
        elif command == 'thank':
            thing = ' '.join(args)
            if thing == 'you':
                respond('you\'re most welcome')
            else:
                respond('thanks, {}!'.format(thing), ping=False)

        if command == 'newday':
            self.bump_topic()

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


def bot_announce(bot, targets, message):
    for target in targets:
        bot.connection.privmsg(target, message)


def celery_listener(bot, uri):
    """Listen for events from Celery, relay to IRC."""
    connection = Connection(uri)

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
    while True:
        last_date, old = date.today(), last_date
        if old and last_date != old:
            bot.bump_topic()
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
    creds = AccountCreationCredentials(**{
        field:
            conf.get(*field.split('_'))
            for field in AccountCreationCredentials._fields
    })
    tasks = get_tasks(celery, credentials=creds)

    rt_password = conf.get('rt', 'password')
    nickserv_password = conf.get('nickserv', 'password')

    # irc bot thread
    bot = CreateBot(tasks, nickserv_password, rt_password)
    bot_thread = threading.Thread(target=bot.start, daemon=True)
    bot_thread.start()

    # celery thread
    celery_thread = threading.Thread(
        target=celery_listener,
        args=(bot, conf.get('celery', 'broker')),
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
