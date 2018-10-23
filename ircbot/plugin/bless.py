"""Blessed be St. Create, progenitor of good code, expeller of bad."""
import random


def register(bot):
    bot.listen(r'bless$', bless)
    bot.listen(r'bless (.*)$', bless_someone, require_mention=True)


def bless(bot, msg):
    """Consecrate the occasion."""
    msg.respond(random.choice((
        'In the name of the compiler, the linker, and the holy runtime, I bless thee.',
        'Not today, Windows.',
        'We are all SysAdmins on this blessed day.',
        'Thou hast made us for thyself, O Server, and our heart is restless until it finds the bug in thee.',
        'The function of prayer is not to influence the printer, but rather to change the nature of the one '
        'who prints.',
    )))


def bless_someone(bot, msg):
    """Have create thank somebody on your behalf."""
    msg.respond(
        'Blessed be {}, in the name of the compiler, the linker, and the holy runtime!'.format(
            msg.match.group(1),
        ), ping=False,
    )
