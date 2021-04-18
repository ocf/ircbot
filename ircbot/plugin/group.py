"""Print group account usernames from subdomain names and vice versa."""
from ocflib.vhost.web import get_vhosts


def register(bot):
    bot.listen(r'^!group(?: (.*))?', group_lookup)
    bot.listen(r'^!subdomain(?: (.*))?', subdomain_lookup)


def group_lookup(bot, msg):
    user = msg.match.group(1)
    vhosts = get_vhosts()
    subdomain = None
    for vhost in vhosts.items():
        if user == vhost[1]['username']:
            subdomain = vhost[0]
    if subdomain is None:
        msg.respond('A subdomain does not exist with this group account.')
        return
    msg.respond('The subdomain name corresponding with ' + user + ' is: ' + subdomain, ping=False)


def subdomain_lookup(bot, msg):
    subdomain = msg.match.group(1)
    user = get_vhosts().get(subdomain)
    if user is None:
        msg.respond('A group account does not exist with this subdomain.')
        return
    user = user.get('username')
    msg.respond('The group account name corresponding with ' + subdomain + ' is: ' + user, ping=False)
