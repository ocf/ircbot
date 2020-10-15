"""Everything is awful."""
import random


BAD_THINGS = (
    '{0} burnt popcorn in the server room',
    '{0} called ABC news',
    '{0} caused a kernel panic',
    '{0} has a small truck',
    '{0} is dead to me',
    '{0} is dying',
    '{0} is the worst',
    '{0} killed net neutrality',
    '{0} sucks',
    '{0} took down NFS',
    '{0} voted for trump',
    '{0} went to stanfurd',
    "{0} is responsible for california's housing crisis",
    '{0} held a gender-reveal party',
    'abolish {0}',
    'society has progressed beyond the need for {0}',
)


def register(bot):
    bot.listen(r'^!sux (.+)', sux)


def sux(bot, msg):
    """Have create complain for you."""
    response = '; '.join(['fuck {0}'] + random.sample(BAD_THINGS, 3))
    msg.respond(
        response.format(msg.match.group(1)),
        ping=False,
    )
