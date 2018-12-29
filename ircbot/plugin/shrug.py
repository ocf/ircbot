"""¯\\_(ツ)_/¯"""


def register(bot):
    bot.listen(r's+h+r+(u+)g+', shrug)


def shrug(bot, msg):
    """Shhhrrrruuuuuuuuuuuuuugggg."""
    width = len(msg.match.group(1))
    msg.respond('¯\\' + ('_' * width) + '(ツ)' + ('_' * width) + '/¯', ping=False)
