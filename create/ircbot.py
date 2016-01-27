#!/usr/bin/env python3
"""IRC bot for printing info and handling commmands for account creation."""
import argparse
import os
import threading

import irc.bot
from celery.events import EventReceiver
from celery.exceptions import TimeoutError
from kombu import Connection


IRC_HOST = 'irc'
IRC_PORT = 6667
IRC_NICKNAME = 'create'

IRC_CHANNELS = ('#rebuild', '#atool')
IRC_CHANNELS_ANNOUNCE = ('#atool',)

bot = None  # sorry


class CreateBot(irc.bot.SingleServerIRCBot):

    def __init__(self, tasks):
        self.tasks = tasks
        irc.bot.SingleServerIRCBot.__init__(
            self,
            [(IRC_HOST, IRC_PORT)],
            IRC_NICKNAME,
            IRC_NICKNAME,
        )

    def on_welcome(self, conn, event):
        for channel in IRC_CHANNELS:
            conn.join(channel)

    def on_pubmsg(self, conn, event):
        is_oper = False

        if event.target in self.channels:
            # event.source is like 'ckuehl!~ckuehl@nitrogen.techxonline.net'
            assert event.source.count('!') == 1
            user, __ = event.source.split('!')

            if user in self.channels[event.target].opers():
                is_oper = True

        assert len(event.arguments) == 1
        msg = event.arguments[0]
        if msg.startswith(IRC_NICKNAME + ' ') or msg.startswith(IRC_NICKNAME + ':'):
            command, *args = msg[len(IRC_NICKNAME) + 1:].strip().split(' ')

            def respond(msg):
                conn.privmsg(event.target, '{}: {}'.format(user, msg))

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
                    except TimeoutError:
                        respond('timed out loading list of requests, sorry!')
                elif command == 'approve':
                    user_name = args[0]
                    self.tasks.approve_request.delay(user_name)
                    respond('approved {}, the account is being created'.format(user_name))
                elif command == 'reject':
                    user_name = args[0]
                    self.tasks.reject_request.delay(user_name)
                    respond('rejected {}, better luck next time'.format(user_name))

            if command.startswith('thank'):
                respond('you\'re welcome')


def bot_announce(targets, message):
    global bot
    if bot:
        for target in targets:
            bot.connection.privmsg(target, message)


def celery_listener(uri):
    """Listen for events from Celery, relay to IRC."""
    connection = Connection(uri)

    def on_account_created(event):
        request = event['request']
        bot_announce(
            IRC_CHANNELS_ANNOUNCE,
            '{user} created ({real_name})'.format(
                user=request['user_name'],
                real_name=request['real_name'],
            ),
        )

    def on_account_submitted(event):
        request = event['request']
        bot_announce(
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
            IRC_CHANNELS_ANNOUNCE,
            '{user} was approved, now pending creation.'.format(
                user=request['user_name'],
            ),
        )

    def on_account_rejected(event):
        request = event['request']
        bot_announce(
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


def main():
    parser = argparse.ArgumentParser(
        description='OCF account creation IRC bot',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '-c',
        '--config',
        default='/etc/ocf-create/ocf-create.conf',
        help='Config file to read from.',
    )
    args = parser.parse_args()
    os.environ['CREATE_CONFIG_FILE'] = args.config

    # these imports require CREATE_CONFIG_FILE set, so we do them inline
    from create.tasks import conf
    from create.tasks import tasks

    # create a thread to run the irc bot
    global bot
    bot = CreateBot(tasks)
    bot_thread = threading.Thread(target=bot.start)
    bot_thread.start()

    # run create listener in main thread
    celery_listener(conf.get('celery', 'broker'))

if __name__ == '__main__':
    main()
