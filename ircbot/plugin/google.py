"""Let me Google that for you."""
import requests


def register(bot):
    bot.listen(r'!g (.+)$', google)


def google(bot, msg):
    """Search Google."""
    query = msg.match.group(1)

    resp = requests.get(
        'https://www.googleapis.com/customsearch/v1',
        params={
            'key': bot.googlesearch_key,
            # The "cx" parameter is the ID of the custom search engine.
            'cx': bot.googlesearch_cx,
            'q': query,
        }
    )
    if resp.status_code != 200:
        msg.respond('error searching google: {.status_code}'.format(resp), ping=False)
    else:
        results = resp.json()
        if len(results.get('items', ())) == 0:
            msg.respond('no results :(', ping=False)
        else:
            item = results['items'][0]
            msg.respond(
                '\x0314{0[title]} \x0F| \x0302{0[link]}'.format(item),
                ping=False,
            )
