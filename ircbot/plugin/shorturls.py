"""Control ocfweb shorturls through ircbot."""
from ircbot import db

KEYWORDS = {'add', 'delete', 'rename', 'replace'}


def register(bot):
    # [!-~] is all printable ascii except spaces
    bot.listen(r'^!shorturl ([!-~]+)', show)
    bot.listen(r'^!shorturl add ([!-~]+) (.+)$', add)
    bot.listen(r'^!shorturl delete ([!-~]+)$', delete)
    bot.listen(r'^!shorturl rename ([!-~]+) ([!-~]+)$', rename)
    bot.listen(r'^!shorturl replace ([!-~]+) (.+)$', replace)


def list(bot):
    """List all shorturls for shorturls help page."""

    with db.cursor(password=bot.mysql_password) as c:
        c.execute('SELECT slug, target FROM shorturls ORDER BY slug')

    for entry in c.fetchall():
        yield entry['slug'], entry['target']


def retrieve(bot, slug):
    """Reusable function to retrieve a shorturl by slug from the DB."""

    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'SELECT target FROM shorturls WHERE slug = %s',
            (slug,),
        )
        target = c.fetchone()

        return target['target'] if target else None


def show(bot, msg):
    """Return a shorturl by slug."""

    slug = msg.match.group(1)

    # special case these so show doesn't trigger on add/delete
    # while still letting the trigger appear anywhere in the msg
    if slug in KEYWORDS:
        return

    target = retrieve(bot, slug)
    if not target:
        msg.respond('shorturl `{}` does not exist.'.format(slug))
    else:
        msg.respond(target['target'], ping=False)


def add(bot, msg):
    """Add a new shorturl."""

    slug = msg.match.group(1)
    target = msg.match.group(2)

    if slug in KEYWORDS:
        msg.respond('`{}` is a reserved keyword.'.format(slug))
        return

    if len(slug) > 255:
        msg.respond('shorturl slugs must be <= 255 characters')
        return

    with db.cursor(password=bot.mysql_password) as c:

        c.execute('SELECT * FROM shorturls WHERE slug = %s', (slug,))
        result = c.fetchone()
        if result is not None:
            msg.respond(
                'shorturl `{}` already exists as {}'.format(
                    result['slug'],
                    result['target'],
                ),
            )
        else:
            c.execute(
                'INSERT INTO shorturls (slug, target) VALUES (%s, %s)',
                (slug, target),
            )
            msg.respond('shorturl added as `{}`'.format(slug))


def delete(bot, msg):
    """Delete a shorturl."""

    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'DELETE FROM shorturls WHERE slug = %s',
            (slug,),
        )
        msg.respond('shorturl `{}` has been deleted.'.format(slug))


def rename(bot, msg):
    """Rename a shorturl."""

    old_slug = msg.match.group(1)
    new_slug = msg.match.group(2)

    if new_slug in KEYWORDS:
        msg.respond('`{}` is a reserved keyword.'.format(new_slug))
        return

    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'UPDATE shorturls SET slug = %s WHERE slug = %s',
            (new_slug, old_slug),
        )
        msg.respond('shorturl `{}` has been renamed to `{}`'.format(old_slug, new_slug))


def replace(bot, msg):
    """Replace the target of a shorturl slug."""

    slug = msg.match.group(1)
    new_target = msg.match.group(2)

    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'UPDATE shorturls SET target = %s WHERE slug = %s',
            (new_target, slug),
        )
        msg.respond('shorturl `{}` updated'.format(slug))
