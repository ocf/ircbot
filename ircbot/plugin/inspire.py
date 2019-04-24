"""Print useless "motivational" quotes."""
from ircbot import db


def register(bot):
    bot.listen(r'^!inspire ?(.*)$', inspire)


def inspire(bot, msg):
    """Print a quote, optionally filtering."""
    term = msg.match.group(1) or ''
    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'SELECT text FROM `inspire` ' +
            'WHERE LOWER(text) LIKE LOWER(%s) ' +
            'ORDER BY RAND() LIMIT 1',
            f'%{term}%',
        )

        quote = c.fetchone()

        msg.respond(quote['text'] if quote else f"Nothing inspirational matching '{term}' found.")
