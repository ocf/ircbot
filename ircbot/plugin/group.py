"""Print group account usernames from domain names and vice versa."""
from ocflib.account.search import user_exists
from ocflib.account.search import user_is_group
from ocflib.vhost.application import get_app_vhosts
from ocflib.vhost.mail import get_mail_vhosts
from ocflib.vhost.mail import vhosts_for_user
from ocflib.vhost.web import get_vhosts
from tld import get_tld


def register(bot):
    bot.listen(r'group (.*)$', group_lookup, require_mention=True)
    bot.listen(r'domain (.*)$', domain_lookup, require_mention=True)


def group_lookup(bot, msg):
    user = msg.match.group(1)
    if not user_exists(user):
        msg.respond('error: account ' + user + ' does not exist', ping=False)
        return
    msg.respond(acc_info(user), ping=False)


def domain_lookup(bot, msg):
    domain = auto_complete(msg.match.group(1))
    user = None
    domain_vhost = get_vhosts().get(domain)
    if domain_vhost is not None:
        user = domain_vhost['username']
    if user is None:
        for web_vhost in get_vhosts().items():
            if domain in web_vhost[1]['aliases']:
                user = web_vhost[1]['username']
                if user is not None:
                    break
    if user is None:
        for mail_vhost in get_mail_vhosts():
            if mail_vhost[1] == domain:
                user = mail_vhost[0]
                if user is not None:
                    break
    if user is None:
        domain_apphost = get_app_vhosts().get(domain)
        if domain_apphost is not None:
            user = domain_apphost['username']
    if user is None:
        for app_vhost in get_app_vhosts().items():
            if domain in app_vhost[1]['aliases']:
                user = app_vhost[1]['username']
                if user is not None:
                    break
    if user is None:
        msg.respond('error: domain ' + domain + ' does not exist in etc/configs', ping=False)
        return
    msg.respond(acc_info(user), ping=False)


def acc_info(user):
    web_vhosts = get_vhosts()
    web_domains = []
    mail_vhosts = vhosts_for_user(user)
    mail_domains = []
    app_vhosts = get_app_vhosts()
    app_domains = []
    for web_vhost in web_vhosts.items():
        if user == web_vhost[1]['username']:
            web_domains.extend([web_vhost[0]] + web_vhost[1]['aliases'])
            continue
    for app_vhost in app_vhosts.items():
        if user == app_vhost[1]['username']:
            app_domains.extend([app_vhost[0]] + app_vhost[1]['aliases'])
            continue
    for mail_vhost in mail_vhosts:
        mail_domains.extend([mail_vhost[1]])
    if web_domains == []:
        web_domains = ['none']
    if mail_vhosts == set():
        mail_domains = ['none']
    if app_domains == []:
        app_domains = ['none']
    user_info_str = 'account: ' + user
    is_group_account_str = ' | is group account: ' + str.lower(str(user_is_group(user)))
    web_domains_str = ' | web vhosts: ' + ', '.join(web_domains)
    mail_domains_str = ' | mail vhosts: ' + ', '.join(mail_domains)
    app_domains_str = ' | app vhosts: ' + ', '.join(app_domains)
    return user_info_str + is_group_account_str + web_domains_str + mail_domains_str + app_domains_str


def auto_complete(s):
    if get_tld('http://' + s, fail_silently=True) is None:
        return s + '.berkeley.edu'
    return s
