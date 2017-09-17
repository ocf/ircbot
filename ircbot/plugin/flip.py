"""The Upside Down."""
import upsidedown


def register(bot):
    bot.listen(
        r'(?:flip|sorry|ban) (.+)$', flip, require_mention=True,
        help='uʍop ǝpısdn ʇxǝʇ dıןɟ',
    )


def flip(text, match, bot, respond):
    respond('(╯°□°）╯︵ ┻━┻ {}'.format(
        upsidedown.transform(match.group(1)),
    ))
