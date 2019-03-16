import re

REGEX = re.compile(r'(?:k#)([0-9]+)')


def register(bot):
    bot.listen(REGEX.pattern, show_topic)


def show_topic(bot, msg):
    for topic in REGEX.findall(msg.text):
        id = int(topic)
        msg.respond('https://ocf.io/k/' + str(id))
