""" Convert characters into full-width text characters"""
from string import ascii_lowercase
from string import ascii_uppercase

widetext_map = {i: i + 0xFEE0 for i in range(0x21, 0x7F)}
space = chr(0x3000)  # space character has unique mapping

# As seen in Samuari Jack
thicc = '卂乃匚刀乇下厶卄工丁长乚从几口尸㔿尺丂丅凵リ山乂丫乙'

# Little hack, because translation tables are just dicts
thicc_map = {
    **str.maketrans(ascii_lowercase, thicc),
    **str.maketrans(ascii_uppercase, thicc),
}


def register(bot):
    bot.listen(r'^!widetext(?: (.*))?', widetext)
    bot.listen(r'^!evenwidertext(?: (.*))?', evenwidertext)
    bot.listen(r'^!superwidetext(?: (.*))?', superwidetext)

    bot.listen(r'^!extrathicc(?: (.*))?', extrathicc)


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


def extrathicc(bot, msg):
    """乇乂丅尺卂 丅卄工匚匚"""
    text = get_text(bot, msg)
    if text != '':
        msg.respond(text.translate(thicc_map), ping=False)


def widetextify(text, width=1):
    translated_words = [''.join(
        [c.translate(widetext_map) + space * (width - 1) for c in word],
    )
        for word in text.split()]
    seperator = space * width
    return seperator.join(translated_words)


def get_text(bot, msg=None):
    text = msg.match.group(1)
    if text is None:
        if len(bot.recent_messages[msg.channel]) == 0:
            return ''
        _, text = bot.recent_messages[msg.channel][0]
    return text
