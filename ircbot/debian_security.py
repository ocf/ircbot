import operator
import re
from collections import namedtuple
from datetime import datetime
from xml.etree import ElementTree

import requests


DSA = namedtuple('DSA', ('number', 'package', 'link', 'description', 'date'))
last_seen = None


def dsa_list():
    req = requests.get('https://www.debian.org/security/dsa-long')
    req.raise_for_status()

    root = ElementTree.fromstring(req.content)
    for item in root.iter('{http://purl.org/rss/1.0/}item'):
        # title is of the form "DSA-3804 linux - security update"
        title = item.find('{http://purl.org/rss/1.0/}title').text
        m = re.match('DSA-(\d+) (.+?) - security update$', title)
        assert m, title
        dsa_num = int(m.group(1))
        package = m.group(2)

        link = item.find('{http://purl.org/rss/1.0/}link').text

        # description has random html tags and whitespace
        description = item.find('{http://purl.org/rss/1.0/}description').text.strip()
        description = description.replace('\n', ' ')
        description = re.sub('<[^<]+>', '', description)  # not secure! but good enough

        date = datetime.strptime(
            item.find('{http://purl.org/dc/elements/1.1/}date').text,
            '%Y-%m-%d',
        )

        yield DSA(
            number=dsa_num,
            package=package,
            link=link,
            description=description,
            date=date,
        )


def summarize(description, limit=256):
    words = description.split()
    line = ''
    for word in words:
        new_line = line + ' ' + word
        if len(new_line) > limit:
            return line.strip() + ' [...]'
        else:
            line = new_line
    return line.strip()


def get_new_dsas():
    """Return new DSA summary lines."""
    global last_seen
    lines = []
    dsas = list(dsa_list())

    if last_seen is not None:
        for dsa in sorted(dsas, key=operator.attrgetter('number')):
            if last_seen < dsa.number:
                lines.append('\x02\x0304[DSA {dsa.number}] {dsa.package} - {dsa.link}'.format(dsa=dsa))
                lines.append('\x0304' + summarize(dsa.description))

    last_seen = max(dsa.number for dsa in dsas)
    return lines
