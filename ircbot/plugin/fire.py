"""A really long winded way of writing return 'Yes'"""
import re

import requests


def register(bot):
    bot.listen(r'^is california on fire(\?)?$', onfire, require_mention=True, flags=re.IGNORECASE)


def onfire(bot, msg):
    req = requests.get(
        'http://iscaliforniaonfire.com/',
    )
    req.raise_for_status()
    msg.respond('Yes' if 'yes' in req.text.lower() else 'No', ping=False)
