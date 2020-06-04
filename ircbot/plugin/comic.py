"""Make references to XKCD easier"""
import re
import urllib.error

import xkcd

REGEX = re.compile(r'(?:xkcd#|xkcd.com/)([0-9]+)')


def register(bot):
    bot.listen(REGEX.pattern, show_comic)


def show_comic(_, msg):
    """Show XKCD comic details."""
    for number in REGEX.findall(msg.text):
        try:
            comic = xkcd.Comic(int(number))
            reply = f"XKCD#{int(number)} | '{comic.getTitle()}' | {comic.getImageLink()} | {comic.getAltText()}"
            msg.respond(reply)
        except urllib.error.HTTPError:
            pass
