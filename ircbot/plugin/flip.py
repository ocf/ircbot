"""The Upside Down."""
import upsidedown


def register(bot):
    bot.listen(r'(?:flip|sorry|ban) (.+)$', flip, require_mention=True)


def flip(text, match, bot, respond):
    """uʍop ǝpısdn ʇxǝʇ dıןɟ"""
    respond('(╯°□°）╯︵ ┻━┻ {}'.format(
        upsidedown.transform(match.group(1)),
    ))
