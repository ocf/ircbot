"""Automatically maintain the topic."""


def register(bot):
    bot.listen(
        r'^newday$', newday, require_mention=True, require_oper=True,
        help="bump the topic as if it's a new day",
    )


def newday(text, match, bot, respond):
    bot.bump_topic()
