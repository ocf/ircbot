"""Approve accounts."""
import random

from celery import exceptions


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
