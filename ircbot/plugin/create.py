"""Approve accounts."""
import random

from celery import exceptions


def register(bot):
    bot.listen(
        r'^approve (.+)$', approve, require_mention=True, require_oper=True,
        help='approve a pending account',
    )
    bot.listen(
        r'^reject (.+)$', reject, require_mention=True, require_oper=True,
        help='reject a pending account',
    )
    bot.listen(
        r'^list$', list_pending, require_mention=True,
        help='list accounts pending approval',
    )
    bot.listen(
        r'^!flip$', flip,
        help='provide an authoritative opinion on whether to approve an account',
    )


def approve(text, match, bot, respond):
    user_name = match.group(1)
    bot.tasks.approve_request.delay(user_name)
    respond('approved {}, the account is being created'.format(user_name))


def reject(text, match, bot, respond):
    user_name = match.group(1)
    bot.tasks.reject_request.delay(user_name)
    respond('rejected {}, better luck next time'.format(user_name))


def list_pending(text, match, bot, respond):
    task = bot.tasks.get_pending_requests.delay()
    try:
        task.wait(timeout=5)
        if task.result:
            for request in task.result:
                respond(request)
        else:
            respond('no pending requests')
    except exceptions.TimeoutError:
        respond('timed out loading list of requests, sorry!')


def flip(text, match, bot, respond):
    respond('my quantum randomness says: {}'.format(
        random.choice(('approve', 'reject')),
    ))
