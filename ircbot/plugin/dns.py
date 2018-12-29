"""Show information about internal and external hosts."""
import ipaddress
import socket

from ocflib.infra import hosts
from ocflib.infra import net


def register(bot):
    bot.listen(r'^host (\S+)$', host, require_mention=True)
    bot.listen(r"^(?:what (?:isn't it|is it not)|(?:dns )?haiku)$", haiku, require_mention=True)


def host(bot, msg):
    """Print information about an internal or external hostname."""
    # TODO: also support reverse DNS lookup if given an IP
    # TODO: ipv6 support
    host = msg.match.group(1).lower().rstrip('.')

    # Find the IP
    if '.' not in host:
        host += '.ocf.berkeley.edu'

    try:
        ip = socket.gethostbyname(host)
    except socket.error as ex:
        msg.respond(str(ex))
        return

    try:
        reverse_dns, _, _ = socket.gethostbyaddr(ip)
    except socket.error:
        reverse_dns = None

    if net.is_ocf_ip(ipaddress.ip_address(ip)):
        ocf_host_info = 'OCF host'

        hosts_from_ldap = hosts.hosts_by_filter('(ipHostNumber={})'.format(ip))
        if hosts_from_ldap:
            ldap, = hosts_from_ldap
            ocf_host_info += ' ({}, puppet env: {})'.format(
                ldap['type'],
                ldap['environment'][0] if 'environment' in ldap else None,
            )
        else:
            ocf_host_info += ' (not in LDAP?)'
    else:
        ocf_host_info = 'not an OCF host'

    msg.respond(
        '{host}: {ip} ({reverse_dns}) | {ocf_host_info}'.format(
            host=host,
            ip=ip,
            reverse_dns=reverse_dns if reverse_dns else 'no reverse dns',
            ocf_host_info=ocf_host_info,
        ), ping=False,
    )


def haiku(bot, msg):
    """https://i.imgur.com/eAwdKEC.png"""
    for line in (
            "it's not dns",
            "there's no way it's dns",
            'it was dns',
    ):
        msg.respond(line, ping=False)
