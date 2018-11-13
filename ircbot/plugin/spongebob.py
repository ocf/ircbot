"""Create a sentence with random capitalization"""
import random


def register(bot):
    bot.listen(r'^!spongebob (.+)', spongemock)


def spongemock(bot, msg):
    """HAVe CReAte mOcK A SEntEnCE."""
    s = ''.join(c if random.random() < 0.5 else c.swapcase() for c in msg.match.group(1))
    msg.respond(s, ping=False)
