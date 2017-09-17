"""Everything is awful."""


def register(bot):
    bot.listen(
        r'^!sux (.+)*', sux,
        help='have create complain for you',
    )


def sux(text, match, bot, respond):
    respond(
        'fuck {0}; {0} sucks; {0} is dying; {0} is dead to me; {0} hit wtc'.format(
            match.group(1)
        ),
        ping=False,
    )
