#!/usr/bin/env python3
"""IRC bot for printing info and handling commmands for account creation."""
import irc.bot


IRC_HOST = 'irc'
IRC_PORT = 6667
IRC_NICKNAME = 'create'

IRC_CHANNELS = ('#rebuild', '#atool')
IRC_CHANNELS_ANNOUNCE = ('#atool',)


class CreateBot(irc.bot.SingleServerIRCBot):

    def __init__(self):
        irc.bot.SingleServerIRCBot.__init__(
            self,
            [(IRC_HOST, IRC_PORT)],
            IRC_NICKNAME,
            IRC_NICKNAME,
        )

    def on_welcome(self, conn, event):
        for channel in IRC_CHANNELS:
            conn.join(channel)

    def on_pubmsg(self, conn, event):
        is_oper = False

        if event.target in self.channels:
            # event.source is like 'ckuehl!~ckuehl@nitrogen.techxonline.net'
            assert event.source.count('!') == 1
            user, __ = event.source.split('!')

            if user in self.channels[event.target].opers():
                is_oper = True

        assert len(event.arguments) == 1
        msg = event.arguments[0]
        if (
            msg.startswith(IRC_NICKNAME + ' ') or
            msg.startswith(IRC_NICKNAME + ':')
        ):
            command = msg[len(IRC_NICKNAME) + 1:].strip()
            conn.privmsg(event.target, command)
            print(is_oper)


def main():
    bot = CreateBot()
    bot.start()


if __name__ == '__main__':
    main()
