"""Print useless "motivational" quotes."""
from ircbot import db


def register(bot):
    bot.listen(
        r'^!inspire ?(.*)$', inspire,
        help='print a quote, optionally filtering',
    )


def inspire(text, match, bot, respond):
    term = match.group(1) or ''
    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'SELECT text FROM `inspire` ' +
            'WHERE LOWER(text) LIKE LOWER(%s) ' +
            'ORDER BY RAND() LIMIT 1',
            '%{}%'.format(term),
        )
        respond(c.fetchone()['text'])
