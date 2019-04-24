"""Show your appreciation."""
import random


def register(bot):
    bot.listen(r'^thanks', thanks, require_mention=True)
    bot.listen(r'thanks,? create', thanks)
    bot.listen(r'^thank (.*)$', thank_someone, require_mention=True)


def thanks(bot, msg):
    """Thank create for being a helpful robot."""
    msg.respond(
        random.choice((
            "you're welcome",
            'you are most welcome',
            'any time',
            'sure thing boss',
        )),
    )


def thank_someone(bot, msg):
    """Have create thank somebody on your behalf."""
    msg.respond('thanks, {}!'.format(msg.match.group(1)), ping=False)
