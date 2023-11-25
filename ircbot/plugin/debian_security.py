import operator
import re
from collections import namedtuple
from datetime import datetime
from typing import List
from xml.etree import ElementTree

import requests


DSA = namedtuple('DSA', ('number', 'revision', 'package', 'link', 'description', 'date'))
last_seen = 5500
last_seen_rev = 1


def dsa_list():
    req = requests.get('https://www.debian.org/security/dsa-long', timeout=30)
    req.raise_for_status()

    root = ElementTree.fromstring(req.content)
    for item in root.iter('{http://purl.org/rss/1.0/}item'):
        # title is of the form "DSA-5535-1 firefox-esr - security update"
        title = item.find('{http://purl.org/rss/1.0/}title')
        assert title is not None
        assert title.text is not None
        # group 1: dsa number, group 2: revision, group 3: optional package name
        # line ends with the type of notice, see DSA-4204, DSA-4205 for examples
        m = re.match(r'DSA-(\d+)-(\d+) ?(.+)? - ', title.text)
        assert m, title.text
        dsa_num = int(m.group(1))
        dsa_rev = int(m.group(2))
        package = m.group(3)
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

        yield DSA(
            number=dsa_num,
            revision=dsa_rev,
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
    global last_seen_rev
    lines: List[str] = []
    # exceptions (including HTTP error codes) are handled in timer.py
    dsas = list(dsa_list())
    # DSA RSS feed is newest first, reverse to make sure the first
    # revision doesn't get skipped if there's a second revision
    dsas.reverse()

    if last_seen_rev is not None:
        if last_seen is not None:
            for dsa in sorted(dsas, key=operator.attrgetter('number')):
                if last_seen < dsa.number or (
                    last_seen == dsa.number
                    and last_seen_rev < dsa.revision
                ):
                    lines.append(
                        (
                            '\x02\x0304[DSA-{dsa.number}-{dsa.revision}] '
                            '{dsa.package} - {dsa.link}'
                        ).format(dsa=dsa),
                    )
                    lines.append('\x0304' + summarize(dsa.description))
                    last_seen = dsa.number
                    last_seen_rev = dsa.revision
    else:
        last_seen_rev = 1

    last_seen = max(dsa.number for dsa in dsas)
    return lines
