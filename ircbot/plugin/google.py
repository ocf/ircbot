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
        },
    )
    if resp.status_code != 200:
        msg.respond(f'error searching google: {resp.status_code}', ping=False)
    else:
        results = resp.json()
        if len(results.get('items', ())) == 0:
            msg.respond('no results :(', ping=False)
        else:
            item = results['items'][0]
            msg.respond(
                f'\x0314{item["title"]} \x0F| \x0302{item["link"]}',
                ping=False,
            )
