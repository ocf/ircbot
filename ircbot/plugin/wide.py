"""Convert characters into full-width text characters."""
import functools
from string import ascii_lowercase
from string import ascii_uppercase

WIDETEXT_MAP = {i: i + 0xFEE0 for i in range(0x21, 0x7F)}

# the space character has unique mapping to become a unicode ideographic space
WIDE_SPACE_VALUE = 0x3000
WIDE_SPACE_CHAR = chr(WIDE_SPACE_VALUE)
SPACE_VALUE = ord(' ')
WIDETEXT_MAP[SPACE_VALUE] = WIDE_SPACE_VALUE

# As seen in Samurai Jack
THICC = '卂乃匚刀乇下厶卄工丁长乚从几口尸㔿尺丂丅凵リ山乂丫乙'


# Little hack, because translation tables are just dicts
LOWER_THICC = {k: v for k, v in str.maketrans(ascii_lowercase, THICC).items() if v is not None}
UPPER_THICC = {k: v for k, v in str.maketrans(ascii_uppercase, THICC).items() if v is not None}
THICC_MAP = {
    **LOWER_THICC,
    **UPPER_THICC,
    SPACE_VALUE: WIDE_SPACE_VALUE,
}


def register(bot):
    bot.listen(
        r'^!w(?:$| )(.*)?',
        functools.partial(widetextify, width=0),
        help_text='ｗｉｄｅｎ　ｔｅｘｔ',
    )
    bot.listen(
        r'^!w2(?:$| )(.*)?',
        functools.partial(widetextify, width=1),
        help_text='ｗ　ｉ　ｄ　ｅ　ｎ　　　ｔ　ｅ　ｘ　ｔ　　　ｍ　ｏ　ｒ　ｅ',
    )
    bot.listen(
        r'^!w3(?:$| )(.*)?',
        functools.partial(widetextify, width=2),
        help_text='ｓ　　ｕ　　ｐ　　ｅ　　ｒ　　　　　ｗ　　ｉ　　ｄ　　ｅ　　　　　ｔ　　ｅ　　ｘ　　ｔ',
    )
    bot.listen(
        r'^!(?:thiccen|extrathicc)(?:$| )(.*)?',
        functools.partial(widetextify, width=0, translation=THICC_MAP),
        help_text='乇乂丅尺卂　丅卄工匚匚　丅乇乂丅',
    )


def get_text(bot, msg):
    previous_message = bot.recent_messages[msg.channel]

    if msg.match.group(1).strip():
        text = msg.match.group(1)
    elif previous_message:
        text = previous_message[0][1]
    else:
        text = ''

    return text.strip()

def is_emoji(c):
    if ord(c) in range(0x1f300, 0x1fadf) or ord(c) in range(0x2700, 0x27bf):
        return True
    else:
        return False



def widetextify(bot, msg, width, translation=WIDETEXT_MAP):
    """ｗｅｌｃｏｍｅ　ｔｏ　ｔｈｅ　ｏｃｆ

    These activate either on text supplied after the trigger,
    or in the event of an unaccompanied trigger, the previous
    message in the channel.
    """
    text = get_text(bot, msg)
    response = ''
    char_is_emoji = False
    if text:

        for i in range(len(text)):
            if is_emoji(text[i]) and i < len(text) - 1:
                if ord(text[i + 1]) == 0x200d or ord(text[i + 1]) == 0xfe0f:
                    response += text[i]
                else:
                    response += text[i] + WIDE_SPACE_CHAR * width
            elif ord(text[i]) == 0x200d:
                    response += text[i]
            else:
                    response += text[i] + WIDE_SPACE_CHAR * width

        msg.respond(''.join(response), ping=False)
