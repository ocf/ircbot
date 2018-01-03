"""Search (or reverse search) for emojis."""
import shlex
import unicodedata


char_mapping = []
for i in range(0x10ffff):
    c = chr(i)
    try:
        name = unicodedata.name(c)
    except ValueError:
        continue
    if unicodedata.category(c).startswith('C'):
        continue
    char_mapping.append((name, c))
char_mapping = tuple(char_mapping)


def register(bot):
    bot.listen(r'^emoji (.+)$', emoji, require_mention=True)
    bot.listen(r'^remoji (.+)$', remoji, require_mention=True)


def emoji(bot, msg):
    """Search for emojis by name."""
    # allow quoted results
    query = ' '.join(shlex.split(msg.match.group(1))).upper()
    ret = ''
    if query == 'DEBIAN':
        ret += '🍥'
    for name, c in char_mapping:
        if query in name:
            ret += c
    if not ret:
        msg.respond('No results 😢')
    elif len(ret) > 50:
        msg.respond('Showing 1-50 of {} results'.format(len(ret)))
        msg.respond(ret[:50])
    else:
        msg.respond(ret)


def remoji(bot, msg):
    """Show names for emojis."""
    query = msg.match.group(1)
    for c in query[:5]:
        try:
            name = unicodedata.name(c)
        except ValueError:
            name = '<<unknown character>>'
        msg.respond('{}: {}'.format(c, name))
    rest = query[5:]
    if rest:
        msg.respond('{} characters remaining: {}'.format(len(rest), rest))
