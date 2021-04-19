"""Print group account usernames from subdomain names and vice versa."""
import re

from ocflib.vhost.mail import get_mail_vhosts
from ocflib.vhost.mail import vhosts_for_user
from ocflib.vhost.web import get_vhosts


def register(bot):
    bot.listen(r'group (.*)$', group_lookup)
    bot.listen(r'subdomain (.*)$', subdomain_lookup)


def group_lookup(bot, msg):
    user = msg.match.group(1)
    vhosts = get_vhosts()
    subdomain = None
    mail_vhost = vhosts_for_user(user) != set()
    response = ''
    for vhost in vhosts.items():
        if user == vhost[1]['username']:
            subdomain = vhost[0]
            continue
    if subdomain is None and not mail_vhost:
        msg.respond('A subdomain is not linked to group account ' + user, ping=False)
        return
    elif subdomain is not None and mail_vhost:
        response = 'Mail and web'
    elif subdomain is not None and not mail_vhost:
        response = 'Web'
    else:
        subdomain = vhosts_for_user(user)
        for i in subdomain:
            subdomain = i[1]
        response = 'Mail'
    msg.respond(response + ' virtual hosting for account "' + user + '" is enabled at ' + subdomain, ping=False)


def subdomain_lookup(bot, msg):
    subdomain = auto_complete(msg.match.group(1))
    user = get_vhosts().get(subdomain)
    mail_vhost_user = None
    response = ''
    for mail_vhost in get_mail_vhosts():
        if mail_vhost[1] == subdomain:
            mail_vhost_user = mail_vhost[0]
            continue
    if user is None and mail_vhost_user is None:
        msg.respond('A group account is not linked to ' + subdomain, ping=False)
        return
    elif user is not None and mail_vhost_user is not None:
        user = user.get('username')
        response = 'Mail and web'
    elif user is not None and mail_vhost_user is None:
        user = user.get('username')
        response = 'Web'
    else:
        user = mail_vhost_user
        response = 'Mail'
    msg.respond(response + ' virtual hosting at ' + subdomain + ' is enabled for account "' + user + '"', ping=False)


def auto_complete(s):
    valid_endings = ['.berkeley.edu', '.org', '.com', '.edu']
    if not any([re.search(valid_ending, s) is not None for valid_ending in valid_endings]):
        return s + '.berkeley.edu'
    return s
