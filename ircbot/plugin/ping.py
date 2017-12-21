"""Check your connection."""
import random


def register(bot):
    bot.listen(r'^[Pp]+[Ii]+[Nn]+[Gg]+$', pong, require_mention=True)


def pong(bot, msg):
    pleased = random.randint(0, 99)
    if pleased:
        msg.respond(
            ''.join([chr(ord(c) + 6)
                     if c.lower() == 'i' else c
                     for c in msg.text]),
            ping=False)
    else:
        msg.respond('not now, please.', ping=False)
