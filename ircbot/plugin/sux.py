"""Everything is awful."""
import random


BAD_THINGS = (
    '{0} called ABC news',
    '{0} caused a kernel panic',
    '{0} is dead to me',
    '{0} is dying',
    '{0} is the worst',
    '{0} killed net neutrality',
    '{0} sucks',
    '{0} took down NFS',
    '{0} voted for trump',
    '{0} went to stanfurd',
)


def register(bot):
    bot.listen(r'^!sux (.+)*', sux)


def sux(bot, msg):
    """Have create complain for you."""
    response = '; '.join(['fuck {0}'] + random.sample(BAD_THINGS, 3))
    msg.respond(
        response.format(msg.match.group(1)),
        ping=False,
    )
