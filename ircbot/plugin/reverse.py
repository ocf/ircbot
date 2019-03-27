"""Scramble the words in your sentence in a readable way."""


def register(bot):
    bot.listen(r'^!reverse(?: (.*))?', reverse)


def reverse(bot, msg):
    """Reverse the sentence."""
    text = msg.match.group(1)
    if text is None:
        if len(bot.recent_messages[msg.channel]) == 0:
            return
        _, text = bot.recent_messages[msg.channel][0]
    newText = ''
    length = len(text)
    for i in range(length):
        newText += text[length - i - 1]
    msg.respond(newText, ping=False)
