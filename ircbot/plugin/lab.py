"""Get information about the lab."""
from ocflib.lab.stats import staff_in_lab
from ocflib.lab.stats import users_in_lab_count


def register(bot):
    bot.listen(r'is ([a-z0-9]+) in the lab', in_lab, require_mention=True)
    bot.listen(r"(who is|who's) in the lab", who_is_in_lab, require_mention=True)
    bot.listen(r'(?i)w+i+t+l+', who_is_in_lab)


def in_lab(bot, msg):
    """Check if a staffer is in the lab."""
    username = msg.match.group(1).strip()
    for session in staff_in_lab():
        if username == session.user:
            msg.respond(f'{username} is in the lab')
            break
    else:
        msg.respond(f'{username} is not in the lab')


def _prevent_ping(staffer):
    """Hack to prevent pinging the person by inserting a zero-width no-break space in their name."""
    return staffer[0] + '\u2060' + staffer[1:]


def who_is_in_lab(bot, msg):
    """Report on who is currently in the lab."""
    staff = {session.user for session in staff_in_lab()}
    total = users_in_lab_count()

    if total != 1:
        are_number_people = f'are {total} people'
    else:
        are_number_people = 'is 1 person'

    if staff:
        staff_list = ': {}'.format(', '.join(sorted(_prevent_ping(staffer) for staffer in staff)))
    else:
        staff_list = ''

    msg.respond(
        'there {} in the lab, including {} staff{}'.format(
            are_number_people,
            len(staff),
            staff_list,
        ),
    )
