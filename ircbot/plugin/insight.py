"""Give automated insight on new technology"""


def register(bot):
    bot.listen(r'^!insight (.+)', insight)


def insight(_, msg):
    """Modern AI based technology insight."""
    s = 'Maybe before we rush to adopt {0} we should stop to consider \
the consequences of blithely giving this technology such a central \
position in our lives.'
    msg.respond(
        s.format(msg.match.group(1)),
        ping=False,
    )
