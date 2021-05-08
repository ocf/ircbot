"""A really long winded way of writing return 'yes'"""
import re

import requests


def register(bot):
    bot.listen(r'^is california on fire(\?)?$', onfire, require_mention=True, flags=re.IGNORECASE)


def onfire(bot, msg):
    req = requests.get(
        'http://iscaliforniaonfire.com/',
    )
    req.raise_for_status()
    msg.respond('yes' if 'yes' in req.text.lower() else 'no', ping=False)
