"""Announce new RT list every day"""
from datetime import datetime

from ocflib.infra.rt import rt_connection
from ocflib.infra.rt import RtTicket

CHANNEL = '#service-comm'
DAYS_OLD = 7
NUM_LIST = 10
# Starting point for recent most tickets to be searched
NUM_START = 10500


def show_tickets(bot):
    """Show RT tickets that need responses."""
    rt = rt_connection(user='create', password=bot.rt_password)
    bot.say(CHANNEL, 'Top 10 new tickets in the help queue that are older than a week:')

    counter = 0
    counter_success = 0
    num_newest_rt = newest_rt_number(rt, NUM_START)
    while counter_success < NUM_LIST:
        ticket_number = num_newest_rt - counter
        ticket = RtTicket.from_number(rt, ticket_number)
        if out_of_range(ticket):
            break

        # Finds the date of a specific ticket
        lines = rt.get(f'https://rt.ocf.berkeley.edu/REST/1.0/ticket/{ticket_number}/view').text.splitlines()
        for line in lines:
            if line.startswith('Created: '):
                ticket_date = line.split(': ', 1)[1]
        ticket_date = datetime.strptime(ticket_date, '%a %b %d %H:%M:%S %Y')

        if ticket.queue == 'help' and ticket.status == 'new' and (datetime.today() - ticket_date).days >= DAYS_OLD:
            bot.say(CHANNEL, str(ticket))
            counter_success += 1
        counter += 1
    bot.say(CHANNEL, 'Completed.')


def out_of_range(ticket):
    if ticket.owner is None and ticket.subject is None and ticket.queue is None and ticket.status is None:
        return True
    return False


def newest_rt_number(rt, start):
    ticket_number = start
    ticket = RtTicket.from_number(rt, ticket_number)
    while not out_of_range(ticket):
        ticket_number += 1
        ticket = RtTicket.from_number(rt, ticket_number)
    return ticket_number - 1
