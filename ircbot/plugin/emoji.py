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


def emoji(text, match, bot, respond):
    """Search for emojis by name."""
    # allow quoted results
    query = ' '.join(shlex.split(match.group(1))).upper()
    ret = ''
    if query == 'DEBIAN':
        ret += '🍥'
    for name, c in char_mapping:
        if query in name:
            ret += c
    if not ret:
        respond('No results 😢')
    elif len(ret) > 50:
        respond('Showing 1-50 of {} results'.format(len(ret)))
        respond(ret[:50])
    else:
        respond(ret)


def remoji(text, match, bot, respond):
    """Show names for emojis."""
    query = match.group(1)
    for c in query[:5]:
        respond('{}: {}'.format(c, unicodedata.name(c)))
    rest = query[5:]
    if rest:
        respond('{} characters remaining: {}'.format(len(rest), rest))
