"""Reverse the sentence."""


def register(bot):
    bot.listen(r'^!reverse(?: (.*))?', reverse)


def reverse(bot, msg):
    """Reverse the sentence."""
    text = msg.match.group(1)
    if text is None:
        if len(bot.recent_messages[msg.channel]) == 0:
            return
        _, text = bot.recent_messages[msg.channel][0]
    newText = ''.join(reversed(text))
    msg.respond(newText, ping=False)
