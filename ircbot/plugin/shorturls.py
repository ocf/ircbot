"""Control ocfweb shorturls through ircbot."""
import pymysql
from ocflib.misc.shorturls import add_shorturl
from ocflib.misc.shorturls import delete_shorturl
from ocflib.misc.shorturls import get_connection as shorturl_db
from ocflib.misc.shorturls import get_shorturl
from ocflib.misc.shorturls import rename_shorturl
from ocflib.misc.shorturls import replace_shorturl


def register(bot):
    bot.listen(r'^!shorturl get (.+)$', show)
    bot.listen(r'^!shorturl add ([^ ]+) (.+)$', add, require_oper=True)
    bot.listen(r'^!shorturl delete ([^ ]+)$', delete, require_oper=True)
    bot.listen(r'^!shorturl rename ([^ ]+) ([^ ]+)$', rename, require_oper=True)
    bot.listen(r'^!shorturl replace ([^ ]+) (.+)$', replace, require_oper=True)


def show(bot, msg):
    """Return a shorturl by slug."""

    slug = msg.match.group(1)

    with shorturl_db() as ctx:
        target = get_shorturl(ctx, slug)

    if not target:
        msg.respond(f'shorturl `{slug}` does not exist.')
    else:
        msg.respond(target, ping=False)


def add(bot, msg):
    """Add a new shorturl."""

    slug = msg.match.group(1)
    target = msg.match.group(2)

    if len(slug) > 100:
        msg.respond('shorturl slugs must be <= 100 characters')
        return

    with shorturl_db(user='ocfircbot', password=bot.mysql_password) as ctx:
        try:
            add_shorturl(ctx, slug, target)
        except pymysql.err.IntegrityError:
            msg.respond(
                'shorturl already exists, did you mean `!shorturl replace`?',
            )
        except ValueError as e:
            msg.respond(e)
        else:
            msg.respond(f'shorturl added as `{slug}`')


def delete(bot, msg):
    """Delete a shorturl."""

    slug = msg.match.group(1)
    with shorturl_db(user='ocfircbot', password=bot.mysql_password) as ctx:
        delete_shorturl(ctx, slug)
        msg.respond(f'shorturl `{slug}` has been deleted.')


def rename(bot, msg):
    """Rename a shorturl."""

    old_slug = msg.match.group(1)
    new_slug = msg.match.group(2)

    with shorturl_db(user='ocfircbot', password=bot.mysql_password) as ctx:
        rename_shorturl(ctx, old_slug, new_slug)
        msg.respond(f'shorturl `{old_slug}` has been renamed to `{new_slug}`')


def replace(bot, msg):
    """Replace the target of a shorturl slug."""

    slug = msg.match.group(1)
    new_target = msg.match.group(2)

    with shorturl_db(user='ocfircbot', password=bot.mysql_password) as ctx:
        replace_shorturl(ctx, slug, new_target)
        msg.respond(f'shorturl `{slug}` updated')
