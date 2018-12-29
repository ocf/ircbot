""" Convert characters into full-width text characters"""
import functools
from string import ascii_lowercase
from string import ascii_uppercase

widetext_map = {i: i + 0xFEE0 for i in range(0x21, 0x7F)}
widetext_map[ord(' ')] = 0x3000  # the space character has unique mapping to become a unicode ideographic space
space = chr(0x3000)

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


def widetextify(bot, msg, width=1):
    """ｗｅｌｃｏｍｅ　ｔｏ　ｔｈｅ　ｏｃｆ"""
    text = get_text(bot, msg)
    if text:
        response = ''.join(
            [
                char.translate(widetext_map) +
                space * (width - 1) for char in text
            ],
        )
        msg.respond(response, ping=False)


widetext = widetextify
evenwidertext = functools.partial(widetextify, width=2)
superwidetext = functools.partial(widetextify, width=3)


def extrathicc(bot, msg):
    """乇乂丅尺卂 丅卄工匚匚"""
    text = get_text(bot, msg)
    if text:
        msg.respond(text.translate(thicc_map), ping=False)


def get_text(bot, msg=None):
    history = bot.recent_messages[msg.channel]
    return (
        msg.match.group(1)
        or history[0][1] if history else None
    )
