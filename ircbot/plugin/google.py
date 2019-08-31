"""Let me Google that for you."""
import requests


class GoogleNoResultsError(Exception):
    pass


def register(bot):
    bot.listen(r'!g (.+)$', google)
    bot.listen(r'!yt (.+)$', youtube)


def google_query(key, cx, query):
    """Searches Google and returns the first result."""
    resp = requests.get(
        'https://www.googleapis.com/customsearch/v1',
        params={
            'key': key,
            # The "cx" parameter is the ID of the custom search engine.
            'cx': cx,
            'q': query,
        },
    )

    resp.raise_for_status()

    results = resp.json()
    if len(results.get('items', ())) == 0:
        raise GoogleNoResultsError

    return results['items'][0]


def irc_search(bot, msg, query):
    try:
        result = google_query(
            bot.googlesearch_key,
            bot.googlesearch_cx,
            query,
        )
        msg.respond(
            f'\x0314{result["title"]} \x0F| \x0302{result["link"]}',
            ping=False,
        )
    except requests.exceptions.HTTPError as e:
        msg.respond(
            f'error searching google: {e.response.status_code}',
            ping=False,
        )
    except GoogleNoResultsError:
        msg.respond('no results :(', ping=False)


def youtube(bot, msg):
    """Search YouTube"""
    query = msg.match.group(1)
    return irc_search(bot, msg, query + ' site:youtube.com')


def google(bot, msg):
    """Search Google."""
    query = msg.match.group(1)
    return irc_search(bot, msg, query)
