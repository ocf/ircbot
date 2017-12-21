"""Check your connection."""
import random


def register(bot):
    bot.listen(r'^p+i+n+g+$', pong, require_mention=True)


def pong(bot, msg):
    pleased = random.randint(0, 99)
    if pleased:
        msg.respond(msg.text.replace('i', 'o'), ping=False)
    else:
        msg.respond('not now, please.', ping=False)
