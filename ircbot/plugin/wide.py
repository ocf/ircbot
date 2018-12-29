""" Convert characters into full-width text characters"""

widetext_map = {i: i + 0xFEE0 for i in range(0x21, 0x7F)}
space = chr(0x3000)  # space character has unique mapping


def register(bot):
    bot.listen(r'^!widetext(?: (.*))?', widetext)
    bot.listen(r'^!evenwidertext(?: (.*))?', evenwidertext)
    bot.listen(r'^!superwidetext(?: (.*))?', superwidetext)


def widetextify(text, width=1):
    translated_words = [''.join(
        [c.translate(widetext_map) + space * (width - 1) for c in word],
    )
        for word in text.split()]
    seperator = space * width
    return seperator.join(translated_words)


def widetext(bot, msg):
    """ｗｅｌｃｏｍｅ　ｔｏ　ｔｈｅ　ｏｃｆ"""
    text = get_text(bot, msg)
    if text != '':
        msg.respond(widetextify(text), ping=False)


def evenwidertext(bot, msg):
    """ｅ　ｖ　ｅ　ｎ　　　ｗ　ｉ　ｄ　ｅ　ｒ"""
    text = get_text(bot, msg)
    if text != '':
        msg.respond(widetextify(text, width=2), ping=False)


def superwidetext(bot, msg):
    """ｏ　　ｍ　　ｇ"""
    text = get_text(bot, msg)
    if text != '':
        msg.respond(widetextify(text, width=3), ping=False)


def get_text(bot, msg=None):
    text = msg.match.group(1)
    if text is None:
        if len(bot.recent_messages[msg.channel]) == 0:
            return ''
        _, text = bot.recent_messages[msg.channel][0]
    return text
