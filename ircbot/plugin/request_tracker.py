"""Print RT ticket information."""
import re
from numpy import reshape

from ocflib.infra.rt import rt_connection
from ocflib.infra.rt import RtTicket



REGEX = re.compile(r'(?:rt#|ocf.io/rt/)(.*)')


def register(bot):
    bot.listen(REGEX.pattern, show_ticket)


def show_ticket(bot, msg):
    """Show RT ticket details."""
    rt = rt_connection(user='create', password=bot.rt_password)
    for ticket in REGEX.findall(msg.text):
        try:
            #recieves many tickets at once from request
            ticks = get_newest(rt, ticket)
            for t in ticks:
                if t.queue == 'security':
                    t = t._replace(subject='(security ticket)')
                msg.respond(str(t))
        except AssertionError:
            pass

def get_newest(connection, url, limit=10, queue='help'):
    """Returns the newest created RT ticket in the given queue
        url is of the format:
        rt#https://rt.ocf.berkeley.edu/REST/1.0/search/ticket?query=<query>1&fields=id,Owner,Status,Queue,Subject
    """
    resp = connection.get(url)
    assert resp.status_code == 200, resp.status_code
    assert '200 Ok' in resp.text

    def is_not_delim(s):
        return s and s != '--'

    txt = resp.text.splitlines()

    def find(header, lines):
        for line in lines:
                if line.startswith(header + ': '):
                    splt = line.split(': ', 1)
                    return splt[1][7:] if 'id' in splt[0] else splt[1]
    
    #filter out response code and whitespace
    lines = [word for word in txt[2:] if is_not_delim(word)]

    #list of multiple tickets
    tickets = []    
    #corresponds to fields in ticket class
    fields = ('id', 'Owner', 'Subject', 'Queue', 'Status')

    lines = lines[:limit*len(fields)]
    lines = reshape(lines, (len(lines)//len(fields), len(fields)))

    tickets = [RtTicket(*[find(f, line) for f in fields]) for line in lines]
    
    return tickets