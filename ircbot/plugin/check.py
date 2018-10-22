"""Show information about OCF users."""
import grp
import string

from ocflib.account import search
from ocflib.infra import ldap


GROUP_COLOR_MAPPING = {
    'ocf': '\x0314',  # gray
    'sorry': '\x0304',  # red
    'opstaff': '\x0303',  # green
    'ocfstaff': '\x0302',  # blue
    'ocfroot': '\x0307',  # orange
}


def register(bot):
    # TODO: these fit the commands, but aren't named all that great...
    bot.listen(r'^check (.+)$', check, require_mention=True)
    bot.listen(r'^checkacct (.+)$', checkacct, require_mention=True)


def check(bot, msg):
    """Print information about an OCF user."""
    user = msg.match.group(1).strip()
    attrs = search.user_attrs(user)

    if attrs is not None:
        groups = [grp.getgrgid(attrs['gidNumber']).gr_name]
        groups.extend(sorted(
            group.gr_name for group in grp.getgrall() if user in group.gr_mem
        ))
        groups = [
            '{}{}\x0f'.format(GROUP_COLOR_MAPPING.get(group, ''), group)
            for group in groups
        ]

        if 'creationTime' in attrs:
            created = attrs['creationTime'].strftime('%Y-%m-%d')
        else:
            created = 'unknown'

        msg.respond(
            '{user} ({uid}) | {name} | created {created} | groups: {groups}'.format(
                user=user,
                uid=attrs['uidNumber'],
                name=attrs['cn'][0],
                created=created,
                groups=', '.join(groups),
            ),
            ping=False,
        )
    else:
        msg.respond('{} does not exist'.format(user), ping=False)


def alphanum(word):
    return ''.join(
        c for c in word.lower() if c in string.ascii_lowercase
    )


def checkacct(bot, msg):
    """Print matching OCF usernames."""
    search_term = msg.match.group(1).strip()
    keywords = search_term.split()

    if len(keywords) > 0:
        search = '(&{})'.format(
            ''.join(
                # all keywords must match either uid or cn
                '(|(uid=*{keyword}*)(cn=*{keyword}*))'.format(
                    keyword=alphanum(keyword),
                )
                for keyword in keywords
            ),
        )

        with ldap.ldap_ocf() as c:
            c.search(
                ldap.OCF_LDAP_PEOPLE,
                search,
                attributes=('uid', 'cn'),
                size_limit=5,
            )

            if len(c.response) > 0:
                msg.respond(
                    ', '.join(sorted(
                        '{} ({})'.format(
                            entry['attributes']['uid'][0],
                            entry['attributes']['cn'][0],
                        )
                        for entry in c.response
                    )),
                )
            else:
                msg.respond('no results found')
