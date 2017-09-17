"""Approve accounts."""
import random

from celery import exceptions


def register(bot):
    bot.listen(r'^approve (.+)$', approve, require_mention=True, require_oper=True)
    bot.listen(r'^reject (.+)$', reject, require_mention=True, require_oper=True)
    bot.listen(r'^list$', list_pending, require_mention=True)
    bot.listen(r'^!flip$', flip)


def approve(text, match, bot, respond):
    """Approve a pending account."""
    user_name = match.group(1)
    bot.tasks.approve_request.delay(user_name)
    respond('approved {}, the account is being created'.format(user_name))


def reject(text, match, bot, respond):
    """Reject a pending account."""
    user_name = match.group(1)
    bot.tasks.reject_request.delay(user_name)
    respond('rejected {}, better luck next time'.format(user_name))


def list_pending(text, match, bot, respond):
    """List accounts pending approval."""
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
    """Provide an authoritative opinion on whether to approva an account."""
    respond('my quantum randomness says: {}'.format(
        random.choice(('approve', 'reject')),
    ))
