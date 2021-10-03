"""Announce new RT list every day"""
from ocflib.infra.rt import rt_connection
from ocflib.infra.rt import RtTicket

NUM_ITER = 10
NUM_LIST = 10500
CHANNEL = '#service-comm'


def show_tickets(bot, date):
    """Show RT tickets that need responses."""
    rt = rt_connection(user='create', password=bot.rt_password)
    bot.say(CHANNEL, f'Top 10 new tickets in the help queue for today ({str(date)}):')

    counter = 0
    counter_success = 0
    num_newest_rt = newest_rt_number(rt, NUM_LIST)
    while counter_success < NUM_ITER:
        ticket_number = num_newest_rt - counter
        ticket = RtTicket.from_number(rt, ticket_number)
        if out_of_range(ticket):
            break
        if ticket.queue == 'help' and ticket.status == 'new':
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
