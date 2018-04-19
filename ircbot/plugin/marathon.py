"""Manage Marathon apps."""
from ocflib.infra.mesos import marathon


def _client(bot):
    return marathon.MarathonClient(*bot.marathon_creds)


def register(bot):
    bot.listen(
        r'^restart ([^ ]+)$',
        restart, require_mention=True, require_privileged_oper=True,
    )


def restart(bot, msg):
    """Restart a Marathon instance."""
    instance = msg.match.group(1)
    client = _client(bot)
    try:
        client.post('/v2/apps/{}/restart'.format(instance), headers={'Content-Type': 'application/json'})
    except AssertionError as ex:
        msg.respond('error: {}'.format(ex))
    else:
        msg.respond('restarted {}'.format(instance))
