from ircbot import db


def rand(mysql_password, respond, arg):
    with db.cursor(password=mysql_password) as c:
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


def _print_quote(respond, quote):
    respond(
        'Quote #{}: {}'.format(quote['id'], quote['quote']),
        ping=False,
    )


def show(mysql_password, respond, arg):
    quote_ids = []

    for a in arg:
        try:
            quote_ids.append(int(a.lstrip('#')))
        except TypeError:
            respond('Not a valid ID: {}'.format(a))
            break
    else:
        with db.cursor(password=mysql_password) as c:
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


def add(mysql_password, respond, arg):
    with db.cursor(password=mysql_password) as c:
        c.execute(
            'INSERT INTO quotes (quote) VALUES (%s)',
            (' '.join(arg),)
        )

    respond('Your quote was added as #{}'.format(c.lastrowid))


def delete(mysql_password, respond, arg):
    if len(arg) > 1:
        respond('You can only delete one quote at a time.')
    else:
        try:
            quote_id = int(arg[0])
        except TypeError:
            respond('Not a valid ID: {}'.format(arg[0]))
        else:
            with db.cursor(password=mysql_password) as c:
                c.execute(
                    'UPDATE quotes SET is_deleted = 1 WHERE id = %s',
                    (quote_id,)
                )
            respond('Quote #{} has been deleted.'.format(quote_id))


def help(mysql_password, respond, arg):
    respond('usage: !quote {rand | add | show <id> | delete <id>}')
