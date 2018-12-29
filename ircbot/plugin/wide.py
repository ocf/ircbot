"""Convert characters into full-width text characters."""
import functools
from string import ascii_lowercase
from string import ascii_uppercase

WIDETEXT_MAP = {i: i + 0xFEE0 for i in range(0x21, 0x7F)}
# the space character has unique mapping to become a unicode ideographic space
WIDETEXT_MAP[ord(' ')] = 0x3000
SPACE = chr(0x3000)

# As seen in Samurai Jack
THICC = '卂乃匚刀乇下厶卄工丁长乚从几口尸㔿尺丂丅凵リ山乂丫乙'

# Little hack, because translation tables are just dicts
THICC_MAP = {
    **str.maketrans(ascii_lowercase, THICC),
    **str.maketrans(ascii_uppercase, THICC),
}


def register(bot):
    bot.listen(r'^!w(.*)?', functools.partial(widetextify, width=0))  # wide text
    bot.listen(r'^!2w(.*)?', functools.partial(widetextify, width=1))  # even wider text
    bot.listen(r'^!3w(.*)?', functools.partial(widetextify, width=2))  # super wide text

    bot.listen(r'^!thiccen(.*)?', thiccen)


def get_text(bot, msg=None):
    previous_message = bot.recent_messages[msg.channel]

    if msg.match.group(1).strip():
        text = msg.match.group(1)
    elif previous_message:
        text = previous_message[0][1]
    else:
        text = ''

    return text.strip()


def widetextify(bot, msg, width):
    """ｗｅｌｃｏｍｅ　ｔｏ　ｔｈｅ　ｏｃｆ

    These activate either on text supplied after the trigger,
    or in the event of an unaccompanied trigger, the previous
    message in the channel.
    """
    text = get_text(bot, msg)
    if text:
        response = (c.translate(WIDETEXT_MAP) + SPACE * width for c in text)
        msg.respond(''.join(response), ping=False)


def thiccen(bot, msg):
    """乇乂丅尺卂 丅卄工匚匚"""
    text = get_text(bot, msg)
    if text:
        msg.respond(text.translate(THICC_MAP), ping=False)
