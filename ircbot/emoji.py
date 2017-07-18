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


def emoji(respond, query):
    # allow quoted results
    query = ' '.join(shlex.split(query)).upper()
    ret = ''
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


def remoji(respond, query):
    for c in query[:5]:
        respond('{}: {}'.format(c, unicodedata.name(c)))
    rest = query[5:]
    if rest:
        respond('{} characters remaining: {}'.format(len(rest), rest))
