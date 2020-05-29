"""Make references to XKCD easier"""
import re

import xkcd

REGEX = re.compile(r'(?:xkcd#|xkcd.com/)([0-9]+)')


def register(bot):
    bot.listen(REGEX.pattern, show_comic)


def show_comic(_, msg):
    """Show XKCD comic details."""
    for number in REGEX.findall(msg.text):
        try:
            comic = xkcd.Comic(int(number))
            reply = f"XKCD#{int(number)} | '{comic.getTitle()}' | {comic.getImageLink()}"
            msg.respond(str(reply))
        except AssertionError:
            pass
