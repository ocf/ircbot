import unicodedata


def remoji(respond, query):
    for c in query[:5]:
        respond('{}: {}'.format(c, unicodedata.name(c)))
    rest = query[5:]
    if rest:
        respond('{} characters remaining: {}'.format(len(rest), rest))
