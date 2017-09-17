"""Show your appreciation."""
import random


def register(bot):
    bot.listen(
        r'^thanks', thanks, require_mention=True,
        help='thank create for being helpful',
    )
    bot.listen(
        r'^thank (.*)$', thank_someone, require_mention=True,
        help='have create thank somebody on your behalf',
    )


def thanks(text, match, bot, respond):
    respond(random.choice((
        "you're welcome",
        'you are most welcome',
        'any time',
        'sure thing boss',
    )))


def thank_someone(text, match, bot, respond):
    respond('thanks, {}!'.format(match.group(1)), ping=False)
