"""Outsource all your decision making to create."""
import random


def register(bot):
    bot.listen(r'^!flip$', flip)
    bot.listen(r'^!8ball( |$)', eightball)
    bot.listen(r'roll (\d+)d(\d+)', roll, require_mention=True)


def flip(bot, msg):
    """Provide an authoritative opinion on whether to approve something."""
    msg.respond('my quantum randomness says: {}'.format(
        random.choice(('approve', 'reject')),
    ))


def eightball(bot, msg):
    """Accurately predict the future using a magic 8-ball."""
    msg.respond(random.choice((
        'it is certain',
        'it is decidedly so',
        'without a doubt',
        'yes - definitely',
        'you may rely on it',
        'as I see it, yes',
        'most likely',
        'outlook good',
        'yes',
        'signs point to yes',
        'reply hazy, try again',
        'ask again later',
        'better not tell you now',
        'cannot predict now',
        'concentrate and ask again',
        "don't count on it",
        'my reply is no',
        'my sources say no',
        'outlook not so good',
        'very doubtful',
    )))


def roll(bot, msg):
    """Roll some dice (e.g. "roll 5d6")."""
    num_dice = int(msg.match.group(1))
    sides = int(msg.match.group(2))

    if not 1 <= num_dice < 50 or sides < 1:
        msg.respond('no way!')
    else:
        results = [random.randint(1, sides) for _ in range(num_dice)]
        msg.respond('i rolled {}, making {}'.format(
            ', '.join(map(str, results)),
            sum(results),
        ))
