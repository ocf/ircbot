"""Is create turing complete?"""
import itertools
import re

import markovify

from ircbot import db

IRC_NICK_RE = r'[a-zA-Z_\-\[\]\^{}|`][a-zA-Z0-9_\-\[\]\\^{}|`]{2,15}'

final_model = None


def register(bot):
    bot.listen(r'turing', markov, flags=re.IGNORECASE, require_mention=True)
    bot.listen(r'^!genmodels', initialize_markov_dataset)

    initialize_markov_dataset(bot)


def markov(bot, msg):
    """Return the best quote ever"""
    if not final_model:
        return
    msg.respond(
        final_model.make_sentence(tries=100),
        ping=False,
    )


def initialize_markov_dataset(bot, msg=None):
    """Rebuild the markov models"""
    with db.cursor(password=bot.mysql_password) as c:
        # Fetch quote data
        c.execute('SELECT quote from quotes WHERE is_deleted = 0')
        quotes = c.fetchall()

        # Fetch inspire data
        c.execute('SELECT text from inspire')
        inspirations = c.fetchall()

    # Normalize the quote data... Get rid of IRC junk
    normalized_quotes_2d = [normalize_quote(d['quote']) for d in quotes]
    flat_quotes = list(itertools.chain(*normalized_quotes_2d))

    # Normalize the inspire data... Just lightly prune authors
    clean_inspirations = [normalize_inspiration(d['text']) for d in inspirations]

    # Create the two models, and combine them, but give OCF quotes more weight
    global final_model
    quotes_model = markovify.NewlineText('\n'.join(flat_quotes))
    inspire_model = markovify.NewlineText('\n'.join(clean_inspirations))
    final_model = markovify.combine([quotes_model, inspire_model], [1.7, 1])


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
