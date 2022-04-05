"""Space tooling for turing.py and quotes.py"""
import re


def insert_space(w):
    halfway = len(re.sub(r'-slack([^A-Za-z0-9_\-\\\[\]{}^`|]|\Z)', r'\1', w)) // 2
    return w[:halfway] + '\u2060' + w[halfway:]


def insert_space_sentence(sentence):
    return ' '.join(map(insert_space, sentence.split()))
