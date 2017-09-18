"""Get information about the lab."""
from ocflib.lab.stats import staff_in_lab


def register(bot):
    bot.listen(r'is ([a-z]+) in the lab', in_lab, require_mention=True)


def in_lab(bot, msg):
    """Check if a staffer is in the lab."""
    username = msg.match.group(1).strip()
    for session in staff_in_lab():
        if username == session.user:
            msg.respond('{} is in the lab'.format(username))
            break
    else:
        msg.respond('{} is not in the lab'.format(username))
