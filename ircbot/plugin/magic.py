"""You're a wizard, Harry."""


def register(bot):
    bot.listen(r'^magic ?(.*)$', magic, require_mention=True)
    bot.listen(r'\bmystery\b', mystery)


def _magic(thing):
    return '(ノﾟοﾟ)ノﾐ★゜・。。・゜゜・。{} 。・゜☆゜・。。・゜'.format(thing)


def magic(text, match, bot, respond):
    """(ノﾟοﾟ)ノﾐ★゜・。。・゜"""
    respond(_magic(match.group(1) or 'magic'), ping=False)


def mystery(text, match, bot, respond):
    """~it is a mystery~"""
    respond(_magic('https://mystery.fuqu.jp/'), ping=False)
