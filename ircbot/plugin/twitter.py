"""Post the contents of linked tweets."""
import requests

API = 'https://api.twitter.com'
bearer_token = None


def register(bot):
    bot.listen(r'https?://(mobile\.)?twitter\.com/[^/]+/status/([0-9]+)', show_tweet)


def _refresh_token(apikeys):
    global bearer_token
    resp = requests.post(
        '{}/oauth2/token'.format(API),
        data={'grant_type': 'client_credentials'},
        auth=apikeys,
    )
    resp.raise_for_status()

    authorization = resp.json()
    assert(authorization['token_type'] == 'bearer')
    bearer_token = authorization['access_token']


def _tweet(apikeys, status_id):
    if bearer_token is None:
        _refresh_token(apikeys)

    resp = requests.get('{}/1.1/statuses/show.json?id={}&tweet_mode=extended'.format(
        API,
        status_id,
    ), headers={
        'Authorization': 'Bearer {}'.format(bearer_token),
    })
    resp.raise_for_status()

    return resp.json()


def _format_tweet(tweet):
    contents = tweet['full_text']
    media = tweet['extended_entities']['media']
    if media:
        contents = contents.replace(
            media[0]['url'],
            ' '.join([medium['media_url_https'] for medium in media]),
        )
    return '@{handle} ({realname}): {contents}'.format(
        handle=tweet['user']['screen_name'],
        realname=tweet['user']['name'],
        contents=contents,
    )


def show_tweet(bot, msg):
    """Show tweet content."""
    tweet = _tweet(bot.twitter_apikeys, msg.match.group(2))
    msg.respond(_format_tweet(tweet), ping=False)
