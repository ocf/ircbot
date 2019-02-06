"""Show the weather."""
import urllib.parse
from bisect import bisect

import requests


def register(bot):
    bot.listen(r'^(?:weather|hot|cold)\s*(-c)?\s?(.*)$', weather, require_mention=True)


def weather(bot, msg):
    """Show weather for a location (defaults to Berkeley)."""
    unit = 'c' if msg.match.group(1) else 'f'
    where = msg.match.group(2).strip() or 'Berkeley, CA'
    location = find_match(where)
    summary = None
    if location:
        summary = get_summary(bot.weather_apikey, location, unit)
    if summary:
        msg.respond(summary, ping=False)
    else:
        msg.respond('idk where {} is'.format(where))


def f2c(temp):
    return int((32 * temp - 32) * 5 / 9)


def icon(temp, unit='f'):
    # it doesn't get cold in the bay area, anything less than 60°F is a snowman
    if temp < (60 if unit == 'f' else f2c(60)):
        return '☃'
    # it doesn't get hot in the bay area, either
    elif temp < (75 if unit == 'f' else f2c(75)):
        return '☀'
    else:
        return '☢'


def color(temp, text=None, unit='f'):
    if text is None:
        text = '{}°{}'.format(temp, unit.capitalize())

    # The temperature values that will make the color different.
    # Default is fahrenheit, and will be converted to celsius if wanted.
    temp_cutoffs = [40, 50, 60, 70, 75, 80, 90, 999]
    if unit == 'c':
        temp_cutoffs = [f2c(temp) for temp in temp_cutoffs]

    # The keys here are the lower bound of these colors, the last key is very
    # large so that it matches anything above the second-to-last key. This
    # also means the first value matches anything under it.
    colors = [
        '\x0312',  # Light blue (< 40)
        '\x0311',  # Light cyan
        '\x0310',  # Teal
        '\x0314',  # Grey
        '\x0F',    # Reset (default text color)
        '\x0307',  # Orange
        '\x0305',  # Maroon
        '\x0304',  # Red (> 90)
    ]
    temp_ranges = {temp_cutoffs[i]: colors[i] for i in range(len(temp_cutoffs))}
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


def get_summary(api_key, result, unit='f'):
    req = requests.get('http://api.wunderground.com/api/{api_key}/forecast{link}.json'.format(
        api_key=api_key,
        link=result['link'],
    ))
    assert req.status_code == 200, req.status_code
    j = req.json()

    if 'forecast' not in j:
        return None

    translation = {'c': 'celsius', 'f': 'fahrenheit'}

    days = []
    for day in j['forecast']['simpleforecast']['forecastday']:
        days.append('{weekday} {low}-{high}'.format(
            weekday=day['date']['weekday_short'],
            low=color(int(day['low'][translation[unit]]), unit=unit),
            high=color(int(day['high'][translation[unit]]), unit=unit),
        ))

    cur = j['forecast']['simpleforecast']['forecastday'][0]
    current = '{conditions}'.format(
        conditions=cur['conditions'],
    )

    return '{name}: {current} {icon}; {days}'.format(
        current=current,
        icon=icon(int(cur['high'][translation[unit]]), unit),
        name=result['name'],
        days=', '.join(days),
    )
