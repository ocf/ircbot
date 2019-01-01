"""Provide OCF image macros, inspired by Phabricator Macros"""
from ircbot import db

KEYWORDS = {'add', 'delete', 'rename', 'replace'}


def register(bot):
    bot.listen(r'#m (\w+)', show)
    bot.listen(r'^#m add (\w+) (.+)$', add)
    bot.listen(r'^#m delete (\w+)$', delete)
    bot.listen(r'^#m rename (\w+) (\w+)$', rename)
    bot.listen(r'^#m replace (\w+) (.+)$', replace)


def show(bot, msg):
    """Return a macro by slug."""
    slug = msg.match.group(1)

    # special case these so show doesn't trigger on add/delete
    # while still letting the trigger appear anywhere in the msg
    if slug in KEYWORDS:
        return

    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'SELECT link FROM macros WHERE slug = %s',
            (slug,),
        )
        macro = c.fetchone()
        if macro is not None:
            msg.respond(macro['link'], ping=False)
        else:
            msg.respond('macro `{}` does not exist.'.format(slug))


def add(bot, msg):
    """Add a new macro."""

    slug = msg.match.group(1)
    link = msg.match.group(2)

    if slug in KEYWORDS:
        msg.respond('`{}` is a reserved keyword.'.format(slug))
        return

    if len(slug) > 50 or len(link) > 100:
        msg.respond('macro slugs must be <= 50 and links <= 100 characters')
        return

    if len(link) > 80:
        msg.respond('please try to keep macro links below 80 characters')

    with db.cursor(password=bot.mysql_password) as c:

        c.execute('SELECT * FROM macros WHERE slug = %s', (slug,))
        result = c.fetchone()
        if result is not None:
            msg.respond(
                'macro `{}` already exists as {}'.format(
                    result['slug'],
                    result['link'],
                ),
            )
        else:
            c.execute(
                'INSERT INTO macros (slug, link) VALUES (%s, %s)',
                (slug, link),
            )
            msg.respond('macro added as `{}`'.format(slug))


def delete(bot, msg):
    """Delete a macro."""

    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'DELETE FROM macros WHERE slug = %s',
            (slug,),
        )
        msg.respond('macro `{}` has been deleted.'.format(slug))


def rename(bot, msg):
    """Rename a macro."""

    old_slug = msg.match.group(1)
    new_slug = msg.match.group(2)

    if new_slug in KEYWORDS:
        msg.respond('`{}` is a reserved keyword.'.format(new_slug))
        return

    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'UPDATE macros SET slug = %s WHERE slug = %s',
            (new_slug, old_slug),
        )
        msg.respond('macro `{}` has been renamed to `{}`'.format(old_slug, new_slug))


def replace(bot, msg):
    """Replace the target of a macro slug."""

    slug = msg.match.group(1)
    new_link = msg.match.group(2)

    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'UPDATE macros SET link = %s WHERE slug = %s',
            (new_link, slug),
        )
        msg.respond('macro `{}` updated'.format(slug))


def list(bot):
    """List all macros for macros help page."""

    with db.cursor(password=bot.mysql_password) as c:
        c.execute('SELECT slug, link FROM macros ORDER BY slug')

    for entry in c.fetchall():
        yield entry['slug'], entry['link']
