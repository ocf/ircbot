"""Provide help information."""


def register(bot):
    bot.listen(r'^help$', help, require_mention=True)
    bot.listen(r'^macros?$', help_macro, require_mention=True)


def help(bot, msg):
    """Provide a link to this help page."""
    msg.respond('https://ircbot.ocf.berkeley.edu/')


def help_macro(bot, msg):
    """Provide a link to the list of macros."""
    msg.respond('https://ircbot.ocf.berkeley.edu/macros')
