"""Is create turing complete?"""
import itertools
import re

import markovify

from ircbot import db

IRC_NICK_RE = r'[a-zA-Z_\-\[\]\^{}|`][a-zA-Z0-9_\-\[\]\\^{}|`]{2,15}'

final_model = None


def register(bot):
    bot.listen(r'turing', markov, flags=re.IGNORECASE, require_mention=True)
    bot.listen(r'^!genmodels', build_models)

    build_models(bot)


def markov(bot, msg):
    """Return the best quote ever"""
    if final_model:
        msg.respond(
            final_model.make_sentence(tries=100),
            ping=False,
        )


def build_models(bot, msg=None):
    """Rebuild the markov models"""
    with db.cursor(password=bot.mysql_password) as c:
        # Fetch quote data
        c.execute('SELECT quote from quotes WHERE is_deleted = 0')
        quotes = c.fetchall()

        # Fetch inspire data
        c.execute('SELECT text from inspire')
        inspirations = c.fetchall()

        # Fetch iconic FOSS rants
        c.execute('SELECT text from rants')
        rants = c.fetchall()

    # Normalize the quote data... Get rid of IRC junk
    normalized_quotes_2d = [normalize_quote(d['quote']) for d in quotes]
    flat_quotes = list(itertools.chain(*normalized_quotes_2d))

    # Normalize the inspire data... Just lightly prune authors
    clean_inspirations = [normalize_inspiration(d['text']) for d in inspirations]

    # Normalize the rant data... just remove ending punctuation
    clean_rants = [normalize_rant(d['text']) for d in rants]

    # Create the three models, and combine them.
    # More heavily weight our quotes and rants
    global final_model
    rants_model = markovify.NewlineText('\n'.join(clean_rants))
    quotes_model = markovify.NewlineText('\n'.join(flat_quotes))
    inspire_model = markovify.NewlineText('\n'.join(clean_inspirations))
    final_model = markovify.combine([quotes_model, rants_model, inspire_model], [2, 1.5, 1])


def normalize_quote(q):
    # Remove "keur:" from start of text
    cleaned = re.sub(r'^\s*{}:\s*'.format(IRC_NICK_RE), '', q)
    # Remove "<@keur>" and "<keur>" and "< keur>"
    cleaned = re.sub(r'<\s*@?{}\s*>:?\s*'.format(IRC_NICK_RE), '', cleaned)
    # Remove "-keur" from the end of text
    cleaned = re.sub(r'\s*\-\s*{}'.format(IRC_NICK_RE), '', cleaned)
    # Remove timestamps
    cleaned = re.sub(r'\[?\d{2}:\d{2}(:?:\d{2})?\]?', '', cleaned)
    # Remove "\\" newline separators
    cleaned = re.sub(r'\\\s', '', cleaned)
    sentences = re.split(r'\.|\?|!', cleaned)
    return [c.strip() for c in sentences if c]


def normalize_inspiration(q):
    # Remove fancy en dash or double dash that start author clause
    cleaned = re.sub('—.*$', '', q)
    cleaned = re.sub('--.*$', '', cleaned)
    # Remove "\\" newline separators
    cleaned = re.sub(r'\\\s', '', cleaned)
    return cleaned.strip()


def normalize_rant(r):
    # Remove sentence ends because we need the newline model
    # so this will match up with our other datasets
    cleaned = re.sub(r'(\.|\?|!)$', '', r)
    return cleaned.strip()
