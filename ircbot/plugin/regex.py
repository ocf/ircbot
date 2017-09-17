"""Replace text."""
import re


def register(bot):
    bot.listen(r'(?:^| )s([!@"#$%&\'*./:;=?\\^_`|~])(.+)\1(.*)\1g?$', replace)


def replace(text, match, bot, respond):
    """Regex-replace some text."""
    old = match.group(2)

    # By default, re.sub processes strings like r'\n' for escapes,
    # turning it into an actual newline. By using a function for
    # the replacement, we avoid the parsing of escape sequences.
    # https://github.com/ocf/ircbot/issues/3
    def new(_):
        return '\x02{}\x02'.format(match.group(3))

    for user, msg in bot.recent_messages:
        try:
            new_msg = re.sub(old, new, msg)
            if new_msg != msg:
                respond('<{}> {}'.format(user, new_msg), ping=False)
                break
        except re.error:
            continue
