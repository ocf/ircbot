"""You're a wizard, Harry."""


def register(bot):
    bot.listen(r'^magic ?(.*)$', magic, require_mention=True)
    bot.listen(r'\bmystery\b|'
               r"\bwhy (do(es)?n't .+ work|(is|are)n't .+ working)\b|"
               r'\bhow do(es)? .+ work\b', mystery)


def _magic(thing):
    return '(ノﾟοﾟ)ノﾐ★゜・。。・゜゜・。{} 。・゜☆゜・。。・゜'.format(thing)


def magic(bot, msg):
    """(ノﾟοﾟ)ノﾐ★゜・。。・゜"""
    msg.respond(_magic(msg.match.group(1) or 'magic'), ping=False)


def mystery(bot, msg):
    """~it is a mystery~"""
    msg.respond(_magic('https://mystery.fuqu.jp/'), ping=False)
