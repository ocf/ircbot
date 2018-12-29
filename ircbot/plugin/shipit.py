"""Your code is probably not ready for production."""
import re


def register(bot):
    bot.listen(r's+h+(i+)p+\s*i+t+', shipit, flags=re.IGNORECASE)


def shipit(bot, msg):
    """shipit anyway!"""
    num = len(msg.match.group(1))
    boat = (
        '.  o ..',
        '    o . o o' + 'oo ' * num,
        '        ...' + 'oo ' * num,
        '          _' + '_[]' * num + '__',
        '       __|_' + 'o_o' * num + '_o\\__',
        '       \\""' + '"""' * num + '"""""/',
        '        \\. ' + '.. ' * num + ' . / ',
        '   ^^^^^^^^' + '^^^' * num + '^^^^^^^^^',
    )

    for line in boat:
        msg.respond(line, ping=False)
