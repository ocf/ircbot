"""Get information about the lab."""
from ocflib.lab.stats import staff_in_lab
from ocflib.lab.stats import users_in_lab_count


def register(bot):
    bot.listen(r'is ([a-z]+) in the lab', in_lab, require_mention=True)
    bot.listen(r"(who is|who's) in the lab", who_is_in_lab, require_mention=True)
    bot.listen(r"@labstaff", ping_lab_staff, require_mention=False)

def in_lab(bot, msg):
    """Check if a staffer is in the lab."""
    username = msg.match.group(1).strip()
    for session in staff_in_lab():
        if username == session.user:
            msg.respond('{} is in the lab'.format(username))
            break
    else:
        msg.respond('{} is not in the lab'.format(username))


def _prevent_ping(staffer):
    """Hack to prevent pinging the person by inserting a zero-width no-break space in their name."""
    return staffer[0] + '\u2060' + staffer[1:]


def who_is_in_lab(bot, msg):
    """Report on who is currently in the lab."""
    staff = {session.user for session in staff_in_lab()}
    total = users_in_lab_count()

    if total != 1:
        are_number_people = 'are {} people'.format(total)
    else:
        are_number_people = 'is 1 person'

    if staff:
        staff_list = ': {}'.format(', '.join(sorted(_prevent_ping(staffer) for staffer in staff)))
    else:
        staff_list = ''

    msg.respond('there {} in the lab, including {} staff{}'.format(
        are_number_people,
        len(staff),
        staff_list,
    ))

def ping_lab_staff(bot, msg):
    """Ping everyone who is currently in the lab."""
    staff = {session.user for session in staff_in_lab()}
    channel_users = bot.channels[msg.channel].users()
    staff_nicks = set() 

    for staff_username in staff:
        staff_nicks = staff_nicks | {nick for nick in channel_users if nick.startswith(staff_username)}
    nicks_string = ', '.join(sorted(staff_nicks))

    msg.respond(msg.text.replace("@labstaff", nicks_string)) 
