"""Your code is probably not ready for production."""
import re


def register(bot):
    bot.listen(r's+h+i+p+\s*i+t+', shipit, flags=re.IGNORECASE)


def shipit(bot, msg):
    """shipit anyway!"""
    msg.respond('.  o ..', ping=False)
    msg.respond('    o . o o.o', ping=False)
    msg.respond('        ...oo', ping=False)
    msg.respond('          __[]__', ping=False)
    msg.respond('       __|_o_o_o\__', ping=False)
    msg.respond('       \\""""""""""/', ping=False)
    msg.respond('        \. ..  . / ', ping=False)
    msg.respond('   ^^^^^^^^^^^^^^^^^^^^', ping=False)
