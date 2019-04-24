"""Provide accurate definitions of people and terms."""
from ircbot import db


def register(bot):
    bot.listen(r'^(what|who) (is|are) (.+)$', what_is, require_mention=True)
    bot.listen(r'^know that (.+?) (is|are) (.+)$', know_that, require_mention=True)


def what_is(bot, msg):
    """Print out the current definition."""
    what_who, is_are, thing = msg.match.groups()

    # Special case: "who is in the lab" should be ignored
    if thing.startswith('in the lab'):
        return

    # Special case: DNS haiku
    if thing.startswith('it not'):
        return

    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'SELECT * FROM what_is WHERE thing = %s',
            (thing,),
        )
        definition = c.fetchone()

    if definition is not None:
        msg.respond('{} {} {}'.format(thing, is_are, definition['what_it_is']), ping=False)
    else:
        msg.respond(f'idk {what_who} {thing} {is_are}', ping=False)


def know_that(bot, msg):
    """Create or update a definition."""
    thing, is_are, what_it_is = msg.match.groups()
    with db.cursor(password=bot.mysql_password) as c:
        c.execute(
            'REPLACE INTO what_is (thing, what_it_is) VALUES (%s, %s)',
            (thing, what_it_is),
        )
    msg.respond(f'okay, {thing} {is_are} {what_it_is}', ping=False)
