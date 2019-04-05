"""Kanboard is the hottest new thing"""
import re

from ocflib.infra.kanboard import KanboardError
from ocflib.infra.kanboard import KanboardTask

REGEX = re.compile(r'(?:k#)([0-9]+)')


def register(bot):
    bot.listen(REGEX.pattern, show_task)


def show_task(bot, msg):
    """Show the Kanboard task and don't break the webserver ;)"""
    for task in REGEX.findall(msg.text):
        try:
            k = KanboardTask.from_number('gstaff', bot.kanboard_apikey, int(task))
            msg.respond(str(k))
        except KanboardError:
            pass
