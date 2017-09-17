"""Provide historical OCF quotes."""
from ircbot import db


def register(bot):
    bot.listen(r'^!quote rand ?(.*)$', rand)
    bot.listen(r'^!quote show (.+)$', show)
    bot.listen(r'^!quote add (.+)$', add)
    bot.listen(r'^!quote delete (.+)$', delete)


def _print_quote(respond, quote):
    respond(
        'Quote #{}: {}'.format(quote['id'], quote['quote']),
        ping=False,
    )


def rand(text, match, bot, respond):
    """Show a random quote, optionally filtered by a search term."""
    arg = match.group(1).split()
    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'SELECT * FROM quotes WHERE is_deleted = 0 ' +
            ' '.join(
                'AND quote LIKE %s'
                for _ in arg
            ) +
            ' ORDER BY RAND() LIMIT 1',
            tuple(
                '%{}%'.format(a)
                for a in arg
            ),
        )
        quote = c.fetchone()

    if quote is not None:
        _print_quote(respond, quote)
    else:
        respond('There are... no quotes?')


def show(text, match, bot, respond):
    """Show quote(s) by ID."""
    arg = match.group(1).split()
    quote_ids = []

    for a in arg:
        try:
            quote_ids.append(int(a.lstrip('#')))
        except ValueError:
            respond('Not a valid ID: {}'.format(a))
            break
    else:
        with db.cursor(password=bot.mysql_password) as c:
            for quote_id in quote_ids:
                c.execute(
                    'SELECT * FROM quotes WHERE id = %s and is_deleted = 0',
                    (quote_id,)
                )
                quote = c.fetchone()
                if quote is not None:
                    _print_quote(respond, quote)
                else:
                    respond('Quote #{} does not exist.'.format(quote_id))


def add(text, match, bot, respond):
    """Add a new quote."""
    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'INSERT INTO quotes (quote) VALUES (%s)',
            (match.group(1),)
        )

    respond('Your quote was added as #{}'.format(c.lastrowid))


def delete(text, match, bot, respond):
    """Delete a quote."""
    arg = match.group(1)
    try:
        quote_id = int(arg)
    except ValueError:
        respond('Not a valid ID: {}'.format(arg))
    else:
        with db.cursor(password=bot.mysql_password) as c:
            c.execute(
                'UPDATE quotes SET is_deleted = 1 WHERE id = %s',
                (quote_id,)
            )
        respond('Quote #{} has been deleted.'.format(quote_id))
