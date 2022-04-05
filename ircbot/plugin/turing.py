"""Is create turing complete?"""
import re

import markovify

from ircbot import db
from ircbot.plugin.space_tooling import insert_space_sentence

final_model = None


def register(bot):
    bot.listen(r'^turing$', markov, flags=re.IGNORECASE, require_mention=True)
    bot.listen(r'^!t$', markov, flags=re.IGNORECASE)
    bot.listen(r'^turing regen(?:erate)?$', generate_model, flags=re.IGNORECASE, require_mention=True)

    generate_model(bot)


def markov(bot, msg):
    """Return the best quote ever."""
    if final_model:
        # This tries to generate a sentence that doesn't "overlap", or
        # share too much similarity with seeded text.
        # Read more here: https://github.com/jsvine/markovify#basic-usage
        sentence = final_model.make_sentence(tries=200)
        if sentence:
            # Put a zero width space in every word to prevent pings.
            # This is also much simpler than using crazy IRC nick regex.
            # Put it in the middle of the word since nicks are quoted
            # using "<@keur>" syntax.  Additionally, remove any -slack at
            # the end of a nick, to avoid inserting a space like
            # abcde|-slack (thus pinging abcde).
            msg.respond(
                insert_space_sentence(sentence),
                ping=False,
            )
        else:
            # This has never happened, but just in case...
            msg.respond(
                'Could not generate sentence. Please try again.',
                ping=True,
            )


def generate_model(bot, msg=None):
    """Set models equal to final_model global variable."""
    global final_model
    final_model = build_model(bot.mysql_password, model_weights=[2, 2, 0.5])


def build_model(db_passwd, model_weights=[1, 1, 1]):
    """Rebuild the markov model using quotes, inspire, and rants databases as seeds."""
    with db.cursor(password=db_passwd) as c:
        # Fetch quote data
        c.execute('SELECT quote FROM quotes WHERE is_deleted = 0')
        quotes = c.fetchall()

        # Fetch inspire data
        c.execute('SELECT text FROM inspire')
        inspirations = c.fetchall()

        # Fetch iconic FOSS rants
        c.execute('SELECT text FROM markov_rants')
        rants = c.fetchall()

    # Normalize the quote data... Get rid of IRC junk
    clean_quotes = [normalize_quote(d['quote']) for d in quotes]

    # Normalize the inspire data... Just lightly prune authors
    clean_inspirations = [normalize_inspiration(d['text']) for d in inspirations]

    # Normalize the rant data... just remove ending punctuation
    clean_rants = [normalize_rant(d['text']) for d in rants]

    # Create the three models, and combine them.
    # More heavily weight our quotes and rants
    rants_model = markovify.NewlineText('\n'.join(clean_rants))
    quotes_model = markovify.NewlineText('\n'.join(clean_quotes))
    inspire_model = markovify.NewlineText('\n'.join(clean_inspirations))
    return markovify.combine([quotes_model, rants_model, inspire_model], model_weights)


def normalize_quote(q):
    # Remove timestamps
    cleaned = re.sub(r'\[?\d{2}:\d{2}(:?:\d{2})?\]?', '', q)
    # Remove "\\" newline separators
    cleaned = re.sub(r'\\\s*', '', cleaned)
    # Trim punctuation from end of quotes
    cleaned = re.sub(r'(\.|\?|!)$', '', cleaned)
    return cleaned


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
