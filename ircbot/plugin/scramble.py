"""Scramble the words in your sentence in a readable way."""
import random
import string


def register(bot):
    bot.listen(r'^!scramble(?: (.*))?', scramble)


def scramble(bot, msg):
    """Srclabme the wdros in yuor senncete in a raadeble way."""
    text = msg.match.group(1)
    if text is None:
        if len(bot.recent_messages[msg.channel]) == 0:
            return
        _, text = bot.recent_messages[msg.channel][0]
    msg.respond(scramble_sentence(text), ping=False)


def scramble_sentence(text):
    ret = word = ''
    for c in text:
        if c.isspace() or c in string.punctuation:
            ret += scramble_word(word) + c
            word = ''
        else:
            word += c
    return ret + scramble_word(word)


def scramble_word(word):
    if len(word) > 3:
        tmp = list(word[1:-1])
        random.shuffle(tmp)
        return word[0] + ''.join(tmp) + word[-1]
    return word
