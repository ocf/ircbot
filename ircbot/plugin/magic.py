"""You're a wizard, Harry."""


def register(bot):
    bot.listen(
        r'^magic ?(.*)$', magic, require_mention=True,
        help='(ノﾟοﾟ)ノﾐ★゜・。。・゜',
    )
    bot.listen(
        r'\bmystery\b', mystery,
        help='~it is a mystery~',
    )


def _magic(thing):
    return '(ノﾟοﾟ)ノﾐ★゜・。。・゜゜・。{} 。・゜☆゜・。。・゜'.format(thing)


def magic(text, match, bot, respond):
    respond(_magic(match.group(1) or 'magic'), ping=False)


def mystery(text, match, bot, respond):
    respond(_magic('https://mystery.fuqu.jp/'), ping=False)
