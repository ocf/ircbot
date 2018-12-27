"""Create a sentence with random capitalization"""
import re
from itertools import cycle
from random import random

memes = frozenset([
    'blockchain', 'coinbase', 'cloud', r'machine\s+learning', r'donald\s+(?:j\.?\s+)?trump',
    r'hacker\s*news', r'web\s*scale',
])


def register(bot):
    bot.listen(r'^!spongebob(?: (.*))?', spongemock)
    bot.listen(r'(.*(?:{}).*)'.format('|'.join(memes)), spongemock, flags=re.IGNORECASE)


def spongebobify(text):
    if len(text) < 2:
        return text

    alpha = 0.25 if len(text) < 10 else 0.45
    fn_set = sorted([str.upper, str.lower], key=lambda _: random())
    fn_cycle = cycle(fn_set)

    spongebob = ''
    case_dup = 1
    transform_fn = next(fn_cycle)
    for c in text:
        spongebob += transform_fn(c)

        if not c.isalpha():
            continue

        # Exponentially decrease the chance of getting same case
        if random() > alpha ** case_dup:
            transform_fn = next(fn_cycle)
            case_dup = 1
        else:
            case_dup += 1

    return spongebob


def spongemock(bot, msg):
    """HaVe CReaTE mOCk A SEnTeNCe."""
    text = msg.match.group(1)
    if text is None:
        if len(bot.recent_messages[msg.channel]) == 0:
            return
        _, text = bot.recent_messages[msg.channel][0]
    msg.respond(spongebobify(text), ping=False)
