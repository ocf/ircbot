import urllib.parse
from bisect import bisect

import requests


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

    temp_ranges = [40, 50, 60, 70, 75, 80, 90]
    colors = [
        '\x0312',  # Light blue (< 40)
        '\x0311',  # Light cyan (40-50)
        '\x0310',  # Teal (50-60)
        '\x0314',  # Grey (60-70)
        '\x0F',   # Reset (default text color, 70-75)
        '\x0307',  # Orange (75-80)
        '\x0305',  # Maroon (80-90)
        '\x0304',  # Red (> 90)
    ]

    # Bisect returns where an element falls in an ordered list, so it can be
    # used for numeric table lookups like this:
    # https://docs.python.org/3/library/bisect.html#other-examples
    color = colors[bisect(temp_ranges, temp)]

    return '{}{}\x03'.format(color, text)


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


def get_summary(api_key, result):
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
            low=color(int(day['low']['fahrenheit'])),
            high=color(int(day['high']['fahrenheit'])),
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
