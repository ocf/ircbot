"""Automatically maintain the topic."""


def register(bot):
    bot.listen(r'^newday$', newday, require_mention=True, require_oper=True)


def newday(bot, msg):
    """Bump the topic, as if it's a new day (mostly for testing)."""
    bot.bump_topic()
