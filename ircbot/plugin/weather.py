"""Show the weather."""
import urllib.parse
from bisect import bisect

import requests


def register(bot):
    bot.listen(r'^(?:weather|hot|cold)(-c)? ?(.*)$', weather, require_mention=True)


def weather(bot, msg):
    """Show weather for a location (defaults to Berkeley)."""
    celsius = 'celsius' if msg.match.group(1) else 'fahrenheit'
    where = msg.match.group(2) or 'Berkeley, CA'
    location = find_match(where)
    summary = None
    if location:
        summary = get_summary(bot.weather_apikey, location, celsius)
    if summary:
        msg.respond(summary, ping=False)
    else:
        msg.respond('idk where {} is'.format(where))


def icon(temp):
    # it doesn't get cold in the bay area, anything less than 60 is a snowman
    if temp < 60:
        return '☃'
    # it doesn't get hot in the bay area, either
    elif temp < 75:
        return '☀'
    else:
        return '☢'


def color(temp, text=None):
    if text is None:
        text = '{}°F'.format(temp)

    # The keys here are the lower bound of these colors, the last key is very
    # large so that it matches anything above the second-to-last key. This
    # also means the first value matches anything under it.
    temp_ranges = {
        40: '\x0312',  # Light blue (< 40)
        50: '\x0311',  # Light cyan
        60: '\x0310',  # Teal
        70: '\x0314',  # Grey
        75: '\x0F',   # Reset (default text color)
        80: '\x0307',  # Orange
        90: '\x0305',  # Maroon
        999: '\x0304',  # Red (> 90)
    }
    temps = sorted(temp_ranges)

    # Bisect returns where an element falls in an ordered list, so it can be
    # used for numeric table lookups like this:
    # https://docs.python.org/3/library/bisect.html#other-examples
    index = bisect(temps, temp)
    color = temp_ranges[temps[index]]

    return '{}{}\x0F'.format(color, text)


def find_match(query):
    req = requests.get('http://autocomplete.wunderground.com/aq?' + urllib.parse.urlencode({
        'query': query,
    }))
    assert req.status_code == 200, req.status_code
    results = req.json()['RESULTS']
    if len(results) > 1:
        result = results[0]
        return {
            'name': result['name'],
            'link': result['l'],
        }


def get_summary(api_key, result, celsius='fahrenheit'):
    req = requests.get('http://api.wunderground.com/api/{api_key}/forecast{link}.json'.format(
        api_key=api_key,
        link=result['link'],
    ))
    assert req.status_code == 200, req.status_code
    j = req.json()

    if 'forecast' not in j:
        return None

    days = []
    for day in j['forecast']['simpleforecast']['forecastday']:
        days.append('{weekday} {low}-{high}'.format(
            weekday=day['date']['weekday_short'],
            low=color(int(day['low'][celsius])),
            high=color(int(day['high'][celsius])),
        ))

    cur = j['forecast']['simpleforecast']['forecastday'][0]
    current = '{conditions}'.format(
        conditions=cur['conditions'],
    )

    return '{name}: {current} {icon}; {days}'.format(
        current=current,
        icon=icon(int(cur['high']['fahrenheit'])),
        name=result['name'],
        days=', '.join(days),
    )
