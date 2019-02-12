"""Pipe the output of a command to the input of the next command."""
from ircbot.ircbot import MatchedMessage


MAX_LENGTH = 5000


def register(bot):
    bot.listen(r'^!pipe (.*)$', pipe)
    bot.listen(r'^!repeat (\d+) (.*)$', repeat)


def pipe(bot, msg):
    """Pipe the output of a command to the input of the next command."""
    commands = filter(None, [s.strip() for s in msg.match.group(1).split('|')])
    stream = ''
    for command in commands:
        if stream:
            command += ' ' + stream
        try:
            stream = run_command(command, bot, msg)
        except Exception as ex:
            msg.respond(str(ex))
            return
    length = len(stream)
    if length > MAX_LENGTH:
        msg.respond('Message length limit exceeded: {} > {}'.format(
            length,
            MAX_LENGTH,
        ))
        return
    msg.respond(stream, ping=False)


def repeat(bot, msg):
    """Repeat a command several times."""
    times = int(msg.match.group(1))
    full_command = msg.match.group(2)
    command = full_command.split()[0]
    if times < 1 or times > 100:
        msg.respond('Invalid times.')
        return
    pipe_command = '!pipe ' + full_command + ('|' + command) * (times - 1)
    msg.respond(run_command(pipe_command, bot, msg), ping=False)


def run_command(command, bot, msg):
    ret = ''
    command_found = False
    for listener in bot.listeners:
        match = listener.pattern.search(command)
        if match is None:
            continue
        command_found = True
        if listener.require_oper or listener.require_privileged_oper:
            raise Exception('Privileged command {} not supported'.format(
                listener.plugin_name,
            ))

        def respond(raw_text, ping=True):
            nonlocal ret
            if len(raw_text) > len(ret):
                ret = raw_text
        stub_msg = MatchedMessage(
            channel=msg.channel,
            text=command,
            raw_text=command,
            match=match,
            is_oper=msg.is_oper,
            nick=msg.nick,
            respond=respond,
        )
        try:
            listener.fn(bot, stub_msg)
        except Exception as ex:
            raise Exception('Command {} not supported: {}'.format(
                listener.plugin_name,
                ex,
            ))
    if not command_found:
        raise Exception('Command {} not found'.format(command.split()[0]))
    return ret
