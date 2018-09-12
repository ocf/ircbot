"""Print Discourse topic information."""
import re

from ocflib.infra.discourse import DiscourseError
from ocflib.infra.discourse import DiscourseTopic


REGEX = re.compile(r'(?:d#|ocf.io/d/)([0-9]+)')


def register(bot):
    bot.listen(REGEX.pattern, show_topic)


def show_topic(bot, msg):
    """Show Discourse topic details."""
    for topic in REGEX.findall(msg.text):
        try:
            d = DiscourseTopic.from_number(bot.discourse_apikey, int(topic))
            msg.respond(str(d))
        except DiscourseError:
            pass
