"""Replace text."""
import re


def register(bot):
    bot.listen(r'(?:^| )s([!@"#$%&\'*./:;=?\\^_`|~])(.+)\1(.*)\1?g?$', replace)


def replace(bot, msg):
    """Regex-replace some text."""
    old = msg.match.group(2)

    # By default, re.sub processes strings like r'\n' for escapes,
    # turning it into an actual newline. By using a function for
    # the replacement, we avoid the parsing of escape sequences.
    # https://github.com/ocf/ircbot/issues/3
    def new(_):
        return '\x02{}\x02'.format(msg.match.group(3))

    for user, recent_msg in bot.recent_messages:
        try:
            new_msg = re.sub(old, new, recent_msg)
            if new_msg != recent_msg:
                msg.respond('<{}> {}'.format(user, new_msg), ping=False)
                break
        except re.error:
            continue
