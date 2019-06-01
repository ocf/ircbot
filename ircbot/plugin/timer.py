"""Run some timers"""
import time
from datetime import date
from textwrap import dedent
from traceback import format_exc

from ircbot.plugin import debian_security

# Check for Debian security announcements every 5 minutes
DSA_FREQ = 5


def register(bot):
    bot.add_thread(timer)


def timer(bot):
    last_date = None
    last_dsa_check = None

    while not (hasattr(bot, 'connection') and bot.connection.connected):
        time.sleep(2)

    while True:
        try:
            last_date, old = date.today(), last_date
            if old and last_date != old:
                bot.bump_topic()

            if last_dsa_check is None or time.time() - last_dsa_check > 60 * DSA_FREQ:
                last_dsa_check = time.time()

                for line in debian_security.get_new_dsas():
                    bot.say('#rebuild', line)
        except Exception:
            error_msg = f'ircbot exception in timer: {format_exc()}'
            bot.say('#rebuild', error_msg)
            bot.handle_error(
                dedent(
                    """
                {error}

                {traceback}
                """
                ).format(
                    error=error_msg,
                    traceback=format_exc(),
                ),
            )

        time.sleep(1)
