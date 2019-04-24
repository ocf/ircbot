"""Print information about Stack Exchange links."""
import collections
import functools
import re
import urllib.parse
from datetime import datetime

import requests


API = 'https://api.stackexchange.com/2.2'


Site = collections.namedtuple('Site', ('api_name', 'name'))
Question = collections.namedtuple(
    'Question',
    (
        'title',
        'owner_name',
        'creation_date',
        'answer_count',
        'score',
    ),
)
Answer = collections.namedtuple('Answer', ('question_id',))


def register(bot):
    # Don't want the bot to crash if we fail to load sites at start (or to
    # delay startup by loading sites), so just listen for all links that look
    # like a Stack Exchange question and filter later to the right domains.
    bot.listen(r'https?://([^/]+)/q(?:uestions)?/([0-9]+)(?:/|$)', question)
    bot.listen(r'https?://([^/]+)/a/([0-9]+)(?:/|$)', answer)


@functools.lru_cache(maxsize=1)
def _sites():
    resp = requests.get(API + '/sites?pagesize=9999')
    resp.raise_for_status()

    domain_from_url = re.compile(r'^https://([^/]+)$')
    return {
        domain_from_url.match(site['site_url']).group(1): Site(
            api_name=site['api_site_parameter'],
            name=site['name'],
        )
        for site in resp.json()['items']
    }


def _question_info(site, question_id):
    resp = requests.get(
        '{}/questions/{}?{}'.format(
            API,
            question_id,
            urllib.parse.urlencode({'site': site.api_name}),
        ),
    )
    resp.raise_for_status()

    questions = resp.json()['items']
    if len(questions) != 1:
        return None
    question, = questions

    return Question(
        title=question['title'],
        owner_name=question['owner']['display_name'],
        creation_date=datetime.fromtimestamp(question['creation_date']),
        answer_count=question['answer_count'],
        score=question['score'],
    )


def _answer_info(site, answer_id):
    resp = requests.get(
        '{}/answers/{}?{}'.format(
            API,
            answer_id,
            urllib.parse.urlencode({'site': site.api_name}),
        ),
    )
    resp.raise_for_status()

    answers = resp.json()['items']
    if len(answers) != 1:
        return None
    answer, = answers

    return Answer(
        question_id=answer['question_id'],
    )


def _format_question(question, site):
    return (
        '\x0314{site.name}:\x03 {question.title} | '
        '\x0303{question.score} votes\x03, \x0302{question.answer_count} answers\x03 | '
        '\x0314{date}\x03'.format(
            question=question,
            site=site,
            date=question.creation_date.strftime('%B %-d, %Y'),
        )
    )


def question(bot, msg):
    """Provide information about a Stack Exchange question."""
    domain, question_id = msg.match.groups()
    site = _sites().get(domain)
    if site is not None:
        question = _question_info(site, question_id)
        msg.respond(_format_question(question, site), ping=False)


def answer(bot, msg):
    """Provide information about a Stack Exchange answer (or really just the question)."""
    domain, answer_id = msg.match.groups()
    site = _sites().get(domain)
    if site is not None:
        answer = _answer_info(site, answer_id)
        question = _question_info(site, answer.question_id)
        msg.respond(_format_question(question, site), ping=False)
