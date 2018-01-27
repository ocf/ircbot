"""Approve accounts."""
import random
import ssl

from celery import exceptions
from celery.events import EventReceiver
from kombu import Connection

from ircbot.ircbot import IRC_CHANNELS_ANNOUNCE
from ircbot.ircbot import IRC_CHANNELS_OPER


def register(bot):
    bot.listen(
        r'^approve (.+)$', approve,
        require_mention=True, require_privileged_oper=True,
    )
    bot.listen(
        r'^reject (.+)$', reject,
        require_mention=True, require_privileged_oper=True,
    )
    bot.listen(r'^list$', list_pending, require_mention=True)
    bot.listen(r'^!flip$', flip)


def approve(bot, msg):
    """Approve a pending account."""
    user_name = msg.match.group(1)
    bot.tasks.approve_request.delay(user_name)
    msg.respond('approved {}, the account is being created'.format(user_name))


def reject(bot, msg):
    """Reject a pending account."""
    user_name = msg.match.group(1)
    bot.tasks.reject_request.delay(user_name)
    msg.respond('rejected {}, better luck next time'.format(user_name))


def list_pending(bot, msg):
    """List accounts pending approval."""
    task = bot.tasks.get_pending_requests.delay()
    try:
        task.wait(timeout=5)
        if task.result:
            for request in task.result:
                msg.respond(request)
        else:
            msg.respond('no pending requests')
    except exceptions.TimeoutError:
        msg.respond('timed out loading list of requests, sorry!')


def flip(bot, msg):
    """Provide an authoritative opinion on whether to approve an account."""
    msg.respond('my quantum randomness says: {}'.format(
        random.choice(('approve', 'reject')),
    ))


def celery_listener(bot, celery, uri):
    """Listen for events from Celery, relay to IRC."""
    connection = Connection(uri, ssl={
        'ssl_ca_certs': '/etc/ssl/certs/ca-certificates.crt',
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
    })

    def bot_announce(targets, message):
        for target in targets:
            bot.say(target, message)

    def on_account_created(event):
        request = event['request']

        if request['calnet_uid']:
            uid_or_gid = 'Calnet UID: {}'.format(request['calnet_uid'])
        elif request['callink_oid']:
            uid_or_gid = 'Callink OID: {}'.format(request['callink_oid'])
        else:
            uid_or_gid = 'No Calnet UID or OID set'

        bot_announce(
            IRC_CHANNELS_ANNOUNCE,
            '{user} created ({real_name}, {uid_or_gid})'.format(
                user=request['user_name'],
                real_name=request['real_name'],
                uid_or_gid=uid_or_gid,
            ),
        )

    def on_account_submitted(event):
        request = event['request']
        bot_announce(
            IRC_CHANNELS_OPER,
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
                app=celery,
                handlers={
                    'ocflib.account_created': on_account_created,
                    'ocflib.account_submitted': on_account_submitted,
                    'ocflib.account_approved': on_account_approved,
                    'ocflib.account_rejected': on_account_rejected,
                },
            )
            recv.capture(limit=None, timeout=None)
