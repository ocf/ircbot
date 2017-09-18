"""The Upside Down."""
import upsidedown


def register(bot):
    bot.listen(r'(?:flip|sorry|ban) (.+)$', flip, require_mention=True)


def flip(bot, msg):
    """uʍop ǝpısdn ʇxǝʇ dıןɟ"""
    msg.respond('(╯°□°）╯︵ ┻━┻ {}'.format(
        upsidedown.transform(msg.match.group(1)),
    ))
