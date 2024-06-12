import operator
import re
from collections import namedtuple
from datetime import datetime
from typing import List
from xml.etree import ElementTree

import requests


DLA = namedtuple('DLA', ('number', 'package', 'link', 'description', 'date'))
last_seen = None


def dla_list():
    req = requests.get('https://www.debian.org/lts/security/dla-long')
    req.raise_for_status()

    root = ElementTree.fromstring(req.content)
    for item in root.iter('{http://purl.org/rss/1.0/}item'):
        # title is of the form "DLA-3804 linux - security update"
        title = item.find('{http://purl.org/rss/1.0/}title')
        assert title is not None
        assert title.text is not None
        # group 1: dla number, group 2: optional package name
        # line ends with the type of notice, see DSA-4204, DSA-4205 for examples
        m = re.match(r'DLA-(\d+) ?(.+)? - ', title.text)
        assert m, title.text
        dla_num = int(m.group(1))
        package = m.group(2)
        link_elt = item.find('{http://purl.org/rss/1.0/}link')
        assert link_elt is not None
        link = link_elt.text

        # description has random html tags and whitespace
        description_elt = item.find('{http://purl.org/rss/1.0/}description')
        assert description_elt is not None
        assert description_elt.text is not None
        description = description_elt.text.strip()
        description = description.replace('\n', ' ')
        description = re.sub('<[^<]+>', '', description)  # not secure! but good enough
        date_elt = item.find('{http://purl.org/dc/elements/1.1/}date')
        assert date_elt is not None
        assert date_elt.text is not None
        date = datetime.strptime(date_elt.text, '%Y-%m-%d')

        yield DLA(
            number=dla_num,
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


def get_new_dlas():
    """Return new DLA summary lines."""
    global last_seen
    lines: List[str] = []
    # exceptions (including HTTP error codes) are handled in timer.py
    dlas = list(dla_list())

    if last_seen is not None:
        for dla in sorted(dlas, key=operator.attrgetter('number')):
            if last_seen < dla.number:
                lines.append('\x02\x0304[DLA {dla.number}] {dla.package} - {dla.link}'.format(dla=dla))
                lines.append('\x0304' + summarize(dla.description))

    last_seen = max(dla.number for dla in dlas)
    return lines
