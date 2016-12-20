import urllib.parse

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
    color = '\x03'
    if temp < 40:
        color += '11'
    elif temp < 50:
        color += '10'
    elif temp < 60:
        color += '14'
    elif temp < 70:
        color += '10'
    elif temp < 75:
        color += '01'
    elif temp < 80:
        color += '07'
    elif temp < 90:
        color += '05'
    else:
        color += '04'
    return '{}{}{}'.format(color, text, '\x0301')


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
