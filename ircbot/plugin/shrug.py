"""¯\_(ツ)_/¯"""


def register(bot):
    bot.listen(
        r's+h+r+(u+)g+', shrug,
        help='helpfully provide shrug emoji',
    )


def shrug(text, match, bot, respond):
    width = len(match.group(1))
    respond('¯\\' + ('_' * width) + '(ツ)' + ('_' * width) + '/¯', ping=False)
