"""Pipe the output of a command to the input of the next command."""
from ircbot.ircbot import MatchedMessage


MAX_LENGTH = 5000


def register(bot):
    bot.listen(r'^!pipe (.*)$', pipe)


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
