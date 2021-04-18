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


def c2f(temp):
    return temp * (9 / 5) + 32


def deg_to_compass(deg):
    """Convert an angle degree to a compass direction with 16 sectors"""

    # deg is from 0-360 (though we use modulo here to wrap just in case we're
    # out of bounds).
    #
    # Each sector is 360/16 = 22.5 degrees wide
    # 0 degrees is in the *middle* of sector 0, so we adjust the input degree
    # by adding 22.5/2 = 11.25.
    #
    # This way, degrees -11.25 through 11.25 get placed in sector 0,
    # 11.25 through 33.75 get placed in sector 1, etc.
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


def icon(temp, unit):
    if unit == 'c':
        temp = c2f(temp)

    # it doesn't get cold in the bay area, anything less than 60°F is a snowman
    if temp < 60:
        return '☃'
    # it doesn't get hot in the bay area, either
    elif temp < 75:
        return '☀'
    else:
        return '☢'


def bold(text):
    return f'\x02{text}\x0F'


def color(temp, unit):
    temp_f = c2f(temp) if unit == 'c' else temp

    text = f'{temp}°{unit.capitalize()}'

    # The temperature values that will make the color different.
    # Default is fahrenheit, and will be converted to celsius if wanted.
    temp_cutoffs = [40, 50, 60, 70, 75, 80, 90, 999]

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
    index = bisect(temps, temp_f)
    color = temp_ranges[temps[index]]

    return f'{color}{text}\x0F'


def calculate_aqi(conc):
    """Calculate US EPA AQI score from PM 2.5 concentration in µg/m3 using
       using the equation at https://forum.airnowtech.org/t/the-aqi-equation/169"""

    conc_lo_cutoffs = [0.0, 12.1, 35.5, 55.5, 150.5, 250.5]
    conc_hi_cutoffs = [12.0, 35.4, 55.4, 150.4, 250.4, 500.4]
    aqi_lo_cutoffs = [0, 51, 101, 151, 201, 301]
    aqi_hi_cutoffs = [50, 100, 150, 200, 300, 500]

    conc = round(conc, 1)
    t_idx = [i for i in range(len(conc_lo_cutoffs)) if conc_lo_cutoffs[i] <= conc][-1]

    conc_lo = conc_lo_cutoffs[t_idx]
    conc_hi = conc_hi_cutoffs[t_idx]
    aqi_lo = aqi_lo_cutoffs[t_idx]
    aqi_hi = aqi_hi_cutoffs[t_idx]

    return round(((aqi_hi - aqi_lo) / (conc_hi - conc_lo)) * (conc - conc_lo) + aqi_lo, 0)


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

    req_aqi = requests.get(
        'http://api.openweathermap.org/data/2.5/air_pollution',
        params={
            **j['coord'],
            'APPID': api_key,
        },
    )
    assert req_aqi.status_code == 200, req_aqi.status_code
    j_aqi = req_aqi.json()

    name = j['name']
    temp = j['main']['temp']
    ico = icon(temp, unit=unit)

    desc = j['weather'][0]['description']

    windspeed = j['wind']['speed']

    winddeg_text = ''
    if 'deg' in j['wind']:
        winddeg = j['wind']['deg']
        winddeg_text = f'{winddeg}° ({deg_to_compass(winddeg)})'

    windunit_text = 'm/s'
    if unit == 'f':
        windunit_text = 'mph'

    wind_text = f'{windspeed} {windunit_text} {winddeg_text}'

    humidity = j['main']['humidity']

    uv_index = j_uv['value']

    aqi_index = calculate_aqi(j_aqi['list'][0]['components']['pm2_5'])

    return '; '.join([
        f'{name}: {bold(color(temp, unit=unit))} {ico} {bold(desc)}',
        f'wind: {bold(wind_text)}',
        f'humidity: {bold(humidity)}%',
        f'UV index: {bold(uv_index)}',
        f'PM2.5 AQI: {bold(aqi_index)}',
    ])
