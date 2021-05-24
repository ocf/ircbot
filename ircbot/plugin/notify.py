"""Ping multiple users at once in notification groups."""
from functools import wraps
from typing import Optional
from typing import Set

from ircbot import db

MAX_DEPTH = 100


class NotifyExpansionLoopError(Exception):
    pass


def register(bot):
    bot.listen(r'!!([^ ]+)', notify)
    bot.listen(r'^!notify show ([^ ]+)$', show)
    bot.listen(r'^!notify showdumb ([^ ]+)$', showdumb)
    bot.listen(r'^!notify create ([^ ]+)$', create)
    bot.listen(r'^!notify delete ([^ ]+)$', delete)
    bot.listen(r'^!notify list$', list_groups)
    bot.listen(r'^!notify addme ([^ ]+)$', addme)
    bot.listen(r'^!notify (?:remove|delete)me ([^ ]+)$', removeme)
    bot.listen(r'^!notify addmembers? ([^ ]+) (.+)$', addmembers)
    bot.listen(r'^!notify addowners? ([^ ]+) (.+)$', addowners)
    bot.listen(r'^!notify (?:remove|delete) ([^ ]+) (.+)$', remove)
    bot.listen(r'^!notify clear ([^ ]+)$', clear)
    bot.listen(r'^!notify add ', addhelp)


def handle_loop_error(fn):
    """Decorate fn to manually catch expansion errors, so they don't send emails."""
    @wraps(fn)
    def handled_fn(bot, msg):
        try:
            return fn(bot, msg)
        except NotifyExpansionLoopError as e:
            msg.respond(str(e))
    return handled_fn


def get_group(cursor, slug: str):
    cursor.execute(
        'SELECT * FROM notify WHERE slug = %s',
        (slug,),
    )
    return cursor.fetchone()


def expand(cursor, targets: str, depth: int = 0) -> Set[str]:
    """Perform expansion on the targets string."""
    result = set()
    target_arr = targets.split(' ')
    for target in target_arr:
        if target[:2] != '!!':
            result.add(target)
        else:
            subtargets = get_all_targets(cursor, target[2:], depth + 1)
            if subtargets is not None:
                result |= subtargets
    return result


def get_all_targets(cursor, slug: str, depth: int = 0) -> Optional[Set[str]]:
    """Expand the full unique list of owners and members of slug."""
    if depth > MAX_DEPTH:
        raise NotifyExpansionLoopError(f'Hit MAX_DEPTH while expanding !!{slug}. Do you have a loop?')

    subtarget = get_group(cursor, slug)
    if subtarget is None:
        return None

    result = set()
    if subtarget['owners'] is not None:
        result |= expand(cursor, subtarget['owners'], depth + 1)
    if subtarget['members'] is not None:
        result |= expand(cursor, subtarget['members'], depth + 1)
    return result


def expand_owners(cursor, targets: str, depth: int = 0) -> Set[str]:
    """Performance expansion on the targets string, only keeping owners."""
    result = set()
    target_arr = targets.split(' ')
    for target in target_arr:
        if target[:2] != '!!':
            result.add(target)
        else:
            subtarget = get_group(cursor, target[:2])
            if subtarget is not None and subtarget['owners'] is not None:
                result |= expand_owners(cursor, subtarget['owners'], depth + 1)
    return result


def deping(target: str) -> str:
    """Insert a 0-length space in target, so as not to ping people."""
    if len(target) < 2:
        return target
    return target[:1] + '\u2060' + target[1:]


def expand_list(cursor, targets: str, depth: int = 0) -> str:
    """Generate an expanded string representing the targets string."""
    if depth > MAX_DEPTH:
        raise NotifyExpansionLoopError(f'Hit MAX_DEPTH while expanding {targets}. Do you have a loop?')

    result = ''
    for target in targets.split(' '):
        if target[:2] != '!!':
            result += deping(target) + ' '

        else:
            subtarget = get_group(cursor, target[2:])
            if subtarget is None:
                result += f'{target}(Not found!) '
            else:
                owners = subtarget['owners'] and expand_list(cursor, subtarget['owners'], depth + 1)
                members = subtarget['members'] and expand_list(cursor, subtarget['members'], depth + 1)
                result += f'{target}({owners} | {members}) '

    # remove trailing space
    return result[:-1]


def is_owner(cursor, respond, group, nick: str) -> bool:
    if group['owners'] is None:
        return False
    try:
        return nick in expand_owners(cursor, group['owners'])
    except NotifyExpansionLoopError as e:
        respond(f'During owner check: {e} Using rudimentary check instead.', ping=False)
        return nick in group['owners'].split(' ')


@handle_loop_error
def notify(bot, msg):
    """Notify all targets (owners and members) in the tagged notificaton group."""
    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        targets = get_all_targets(c, slug)
        if targets is not None:
            targets_str = ' '.join(targets)
            msg.respond(f'{slug}: {targets_str}', ping=False)


@handle_loop_error
def show(bot, msg):
    """Show owners and members of the notification group."""
    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        group = get_group(c, slug)
        if group is None:
            msg.respond(f'{slug} not found.')
            return
        for attr in ('owners', 'members'):
            if group[attr] is None:
                msg.respond(f'{slug} has no {attr}', ping=False)
            else:
                targets = expand_list(c, group[attr])
                msg.respond(f'{slug} {attr}: {targets}', ping=False)


def showdumb(bot, msg):
    """Show the notification group, but don't expand subgroups."""
    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        group = get_group(c, slug)
        if group is None:
            msg.respond(f'{slug} not found.')
            return
        for attr in ('owners', 'members'):
            if group[attr] is None:
                msg.respond(f'{slug} has no {attr}', ping=False)
            else:
                targets = [deping(target) for target in group[attr].split(' ')]
                joined_targets = ' '.join(targets)
                msg.respond(f'{slug} {attr}: {joined_targets}', ping=False)


def create(bot, msg):
    """Create a new notification group."""
    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        existing = get_group(c, slug)
        if existing is not None:
            msg.respond(f'{slug} already exists.')
            return

        c.execute(
            'INSERT INTO notify (slug, owners) VALUES (%s, %s)',
            (slug, msg.nick),
        )
        msg.respond(f'Empty group "{slug}" added. You are the only owner.')


@handle_loop_error
def delete(bot, msg):
    """Delete a notifcation group."""
    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        group = get_group(c, slug)
        if group is None:
            msg.respond('No such notification group.')
            return

        if not msg.is_oper and not is_owner(c, msg.respond, group, msg.nick):
            msg.respond(f'You can\'t delete {slug}, since you\'re neither an oper, nor an owner of the group.')
            return

        c.execute(
            'DELETE FROM notify WHERE slug = %s',
            (slug,),
        )
        msg.respond(f'{slug} has been deleted.')


def list_groups(bot, msg):
    """List all notification groups."""
    with db.cursor(password=bot.mysql_password) as c:
        c.execute('SELECT slug FROM notify')
        slugs = sorted(group['slug'] for group in c.fetchall())
        msg.respond(' '.join(slugs))


def addme(bot, msg):
    """Add yourself to a notification group as a member."""
    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        group = get_group(c, slug)
        if group is None:
            msg.respond('No such notification group.')
            return

        # If you're already a _direct_ owner or member of this group, do nothing.
        if group['owners'] and msg.nick in group['owners'].split(' '):
            msg.respond(f'You\'re already an owner of {slug}!')
            return

        members = []
        if group['members']:
            members = group['members'].split(' ')

        if msg.nick in members:
            msg.respond(f'You\'re already a member of {slug}!')
            return

        members.append(msg.nick)

        c.execute(
            'UPDATE notify SET members = %s WHERE slug = %s',
            (' '.join(members), slug),
        )
        msg.respond(f'Added you to {slug}, as a member.')


def removeme(bot, msg):
    """Remove yourself from a notification group."""
    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        group = get_group(c, slug)
        if group is None:
            msg.respond('No such notification group.')
            return

        # If you're already a _direct_ owner or member of this group, do nothing.
        if group['owners'] and msg.nick in group['owners'].split(' '):
            msg.respond(
                f'You\'re an owner of {slug}. ' +
                'If you\'re sure you want to remove yourself, please use !notify remove.',
            )
            return

        if group['members'] is None:
            msg.respond(f'You\'re not a member of {slug}!')
            return

        members = group['members'].split(' ')
        if msg.nick not in members:
            msg.respond(f'You\'re not a member of {slug}!')
            return

        members = [m for m in members if m != msg.nick]

        c.execute(
            'UPDATE notify SET members = %s WHERE slug = %s',
            (' '.join(members), slug),
        )
        msg.respond(f'Removed you to from the member list for {slug}.')


def addmembers(bot, msg):
    """Add member(s) to a notification group."""
    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        group = get_group(c, slug)
        if group is None:
            msg.respond('No such notification group.')
            return

        if not msg.is_oper and not is_owner(c, msg.respond, group, msg.nick):
            msg.respond(f'You can\'t add to {slug}, since you\'re neither an oper, nor an owner of the group.')
            return

        members = []
        if group['members'] is not None:
            members = group['members'].split(' ')
        owners = []
        if group['owners'] is not None:
            owners = group['owners'].split(' ')

        present = []
        added = []
        for nick in filter(lambda s: s != '', msg.match.group(2).split(' ')):
            if nick in members or nick in owners:
                present.append(nick)
            else:
                members.append(nick)
                added.append(nick)

        if len(present) > 0:
            present_str = ', '.join(present)
            was_plural = 'were' if len(present) > 1 else 'was'
            msg.respond(f'{present_str} {was_plural} already in {slug}.')

        if len(added) == 0:
            return

        c.execute(
            'UPDATE notify SET members = %s WHERE slug = %s',
            (' '.join(members), slug),
        )

        added_str = ', '.join(added)
        if len(added) > 1:
            msg.respond(f'{added_str} were added to {slug} as members.')
        else:
            msg.respond(f'{added_str} was added to {slug} as a member.')


def addowners(bot, msg):
    """Add owner(s) to a notification group."""
    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        group = get_group(c, slug)
        if group is None:
            msg.respond('No such notification group.')
            return

        if not msg.is_oper and not is_owner(c, msg.respond, group, msg.nick):
            msg.respond(f'You can\'t add to {slug}, since you\'re neither an oper, nor an owner of the group.')
            return

        members = []
        if group['members'] is not None:
            members = group['members'].split(' ')
        owners = []
        if group['owners'] is not None:
            owners = group['owners'].split(' ')

        present = []
        moved = []
        added = []
        for nick in filter(lambda s: s != '', msg.match.group(2).split(' ')):
            if nick in members:
                members.remove(nick)
                owners.append(nick)
                moved.append(nick)
            elif nick in owners:
                present.append(nick)
            else:
                owners.append(nick)
                added.append(nick)

        if len(present) > 0:
            present_str = ', '.join(present)
            if len(present) > 1:
                msg.respond(f'{present_str} were already owners of {slug}.')
            else:
                msg.respond(f'{present_str} was already an owner of {slug}.')

        if len(added) == 0 and len(moved) == 0:
            return

        c.execute(
            'UPDATE notify SET owners = %s, members = %s WHERE slug = %s',
            (' '.join(owners), ' '.join(members), slug),
        )

        if len(moved) > 0:
            moved_str = ', '.join(moved)
            if len(moved) > 1:
                msg.respond(f'{moved_str} were moved from members of {slug} to owners.')
            else:
                msg.respond(f'{moved_str} was moved from a member of {slug} to an owner.')

        if len(added) > 0:
            added_str = ', '.join(added)
            if len(added) > 1:
                msg.respond(f'{added_str} were added to {slug} as owners.')
            else:
                msg.respond(f'{added_str} was added to {slug} as an owner.')


def remove(bot, msg):
    """Remove targets from a notification group, for both owners and members."""
    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        group = get_group(c, slug)
        if group is None:
            msg.respond('No such notification group.')
            return

        if not msg.is_oper and not is_owner(c, msg.respond, group, msg.nick):
            msg.respond(f'You can\'t remove from {slug}, since you\'re neither an oper, nor an owner of the group.')
            return

        members = group['members'] and group['members'].split(' ')
        owners = group['owners'] and group['owners'].split(' ')

        missing = []
        former_members = []
        former_owners = []
        for nick in filter(lambda s: s != '', msg.match.group(2).split(' ')):
            if members and nick in members:
                members.remove(nick)
                former_members.append(nick)
            elif owners and nick in owners:
                owners.remove(nick)
                former_owners.append(nick)
            else:
                missing.append(nick)

        if len(missing) > 0:
            missing_str = ', '.join(missing)
            was_plural = 'were' if len(missing) > 1 else 'was'
            msg.respond(f'{missing_str} {was_plural} not in {slug}.')

        if len(former_owners) == 0 and len(former_members) == 0:
            return

        sql_owners = owners
        if owners is not None:
            sql_owners = ' '.join(owners)
        sql_members = members
        if members is not None:
            sql_members = ' '.join(members)

        c.execute(
            'UPDATE notify SET owners = %s, members = %s WHERE slug = %s',
            (sql_owners, sql_members, slug),
        )

        if len(former_owners) > 0:
            owners_str = ', '.join(former_owners)
            if len(former_owners) > 1:
                msg.respond(f'{owners_str} were removed as owners of {slug}.')
            else:
                msg.respond(f'{owners_str} was removed as an owner of {slug}.')

        if len(former_members) > 0:
            members_str = ', '.join(former_members)
            if len(former_members) > 1:
                msg.respond(f'{members_str} were removed as members of {slug}.')
            else:
                msg.respond(f'{members_str} was removed as a member of {slug}.')


def clear(bot, msg):
    """Reset a notification group, clearing all members."""
    slug = msg.match.group(1)
    with db.cursor(password=bot.mysql_password) as c:
        group = get_group(c, slug)
        if group is None:
            msg.respond('No such notification group.')
            return

        if not msg.is_oper and not is_owner(c, msg.respond, group, msg.nick):
            msg.respond(f'You can\'t clear {slug}, since you\'re neither an oper, nor an owner of the group.')
            return

        c.execute(
            'UPDATE notify SET owners = %s, members = NULL WHERE slug = %s',
            (msg.nick, slug),
        )

        msg.respond(f'{slug} has been cleared. You are now the only owner, and there are no members.')


def addhelp(bot, msg):
    """Use create, addmembers, or addowners instead."""
    msg.respond('Did you mean create, addmember(s), or addowner(s)?')
