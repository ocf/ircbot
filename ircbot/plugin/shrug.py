"""¯\_(ツ)_/¯"""


def register(bot):
    bot.listen(r's+h+r+(u+)g+', shrug)


def shrug(text, match, bot, respond):
    """Shhhrrrruuuuuuuuuuuuuugggg."""
    width = len(match.group(1))
    respond('¯\\' + ('_' * width) + '(ツ)' + ('_' * width) + '/¯', ping=False)
