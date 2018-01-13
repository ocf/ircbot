"""Join/leave channels."""
from ircbot import db
from ircbot.ircbot import IRC_CHANNELS_ANNOUNCE
from ircbot.ircbot import IRC_CHANNELS_JOIN_MYSQL
from ircbot.ircbot import IRC_CHANNELS_OPER


def register(bot):
    bot.listen(r'^join (#[a-zA-Z0-9\-_#]+)$', join, require_mention=True)
    bot.listen(r'^leave$', leave, require_mention=True)

    if IRC_CHANNELS_JOIN_MYSQL:
        with db.cursor(password=bot.mysql_password) as c:
            c.execute('SELECT channel FROM channels')
            bot.extra_channels |= {row['channel'] for row in c}


def join_channel(bot, channel):
    if IRC_CHANNELS_JOIN_MYSQL:
        with db.cursor(password=bot.mysql_password) as c:
            c.execute(
                'INSERT IGNORE INTO channels (channel) VALUES (%s)',
                (channel,)
            )
    bot.connection.join(channel)


def on_invite(bot, conn, event):
    channel, = event.arguments
    join_channel(bot, channel)


def join(bot, msg):
    """Join a new channel.

    This is mostly for people on Slack. People on IRC can just /invite the bot.
    """
    join_channel(bot, msg.match.group(1))


def leave(bot, msg):
    """Leave the current channel."""
    if msg.channel in IRC_CHANNELS_OPER | IRC_CHANNELS_ANNOUNCE:
        msg.respond("can't leave {}!".format(msg.channel))
    else:
        with db.cursor(password=bot.mysql_password) as c:
            c.execute(
                'DELETE FROM channels WHERE channel = %s',
                (msg.channel,)
            )
        bot.connection.part(msg.channel)
