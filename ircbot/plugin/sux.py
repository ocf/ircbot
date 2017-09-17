"""Everything is awful."""


def register(bot):
    bot.listen(r'^!sux (.+)*', sux)


def sux(text, match, bot, respond):
    """Have create complain for you."""
    respond(
        'fuck {0}; {0} sucks; {0} is dying; {0} is dead to me; {0} hit wtc'.format(
            match.group(1)
        ),
        ping=False,
    )
