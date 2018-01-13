"""Check your connection."""
import random
import re


def register(bot):
    bot.listen(r'^p+i+n+g+$', pong, flags=re.IGNORECASE, require_mention=True)


def pong(bot, msg):
    """Respond to a ping."""
    pleased = random.randint(0, 99)
    if pleased:
        msg.respond(
            msg.text.replace('i', 'o').replace('I', 'O'),
            ping=False,
        )
    else:
        msg.respond('not now, please.', ping=False)
