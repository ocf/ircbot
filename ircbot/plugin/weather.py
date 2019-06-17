"""Show the weather."""
from bisect import bisect

import requests


def register(bot):
    bot.listen(r'^(?:weather|hot|cold)\s*(-c)?\s?(.*)$', weather, require_mention=True)


def weather(bot, msg):
    """Show weather for a location (defaults to Berkeley).
    Add the -c flag for celsius output."""
    unit = 'c' if msg.match.group(1) else 'f'
    where = msg.match.group(2).strip() or 'Berkeley'
    summary = get_summary(bot.weather_apikey, where, unit)
    if summary:
        msg.respond(summary, ping=False)
    else:
        msg.respond(f'idk where {where} is')


def f2c(temp):
    return int((32 * temp - 32) * 5 / 9)


def deg_to_compass(deg):
    sector = int((deg + 11.25) // 22.5) % 16
    return [
        'N',
        'NNE',
        'NE',
        'ENE',
        'E',
        'ESE',
        'SE',
        'SSE',
        'S',
        'SSW',
        'SW',
        'WSW',
        'W',
        'WNW',
        'NW',
        'NNW',
    ][sector]


def icon(temp, unit='f'):
    # it doesn't get cold in the bay area, anything less than 60°F is a snowman
    if temp < (60 if unit == 'f' else f2c(60)):
        return '☃'
    # it doesn't get hot in the bay area, either
    elif temp < (75 if unit == 'f' else f2c(75)):
        return '☀'
    else:
        return '☢'


def bold(text):
    return f'\x02{text}\x0F'


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
        '',        # None (default text color)
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

    return f'{color}{text}\x0F'


def get_summary(api_key, location, unit='f'):
    translation = {'c': 'metric', 'f': 'imperial'}
    req = requests.get(
        'https://api.openweathermap.org/data/2.5/weather',
        params={
            'q': location,
            'units': translation[unit],
            'APPID': api_key,
        },
    )
    if req.status_code == requests.codes.not_found:
        return None

    assert req.status_code == 200, req.status_code
    j = req.json()

    req_uv = requests.get(
        'https://api.openweathermap.org/data/2.5/uvi',
        params={
            **j['coord'],
            'APPID': api_key,
        },
    )
    assert req_uv.status_code == 200, req_uv.status_code
    j_uv = req_uv.json()

    name = j['name']
    temp = j['main']['temp']
    ico = icon(temp, unit=unit)
    desc = j['weather'][0]['description']

    windspeed = j['wind']['speed']
    winddeg = j['wind']['deg']
    wind_text = f'{windspeed}m/s {winddeg}° ({deg_to_compass(winddeg)})'

    humidity = j['main']['humidity']

    uv_index = j_uv['value']

    return '; '.join([
        f'{name}: {bold(color(temp, unit=unit))} {ico} {bold(desc)}',
        f'wind: {bold(wind_text)}',
        f'humidity: {bold(humidity)}',
        f'UV index: {bold(uv_index)}',
    ])
