"""Run some timers"""
import time
from datetime import date
from textwrap import dedent
from traceback import format_exc

from ircbot.plugin import debian_security

# Check for Debian security announcements every 5 minutes
# If a check fails, we bump add another 10 minutes, until
# the maximum of 120 minutes
DSA_FREQ_DEFAULT = 5
DSA_FREQ_BACKOFF = 10
DSA_FREQ_MAX = 120


def register(bot):
    bot.add_thread(timer)


def timer(bot):
    exception_count = 0
    dsa_freq = DSA_FREQ_DEFAULT

    last_date = None
    last_dsa_check = None

    while not (hasattr(bot, 'connection') and bot.connection.connected):
        time.sleep(2)

    while True:
        try:
            last_date, old = date.today(), last_date
            if old and last_date != old:
                bot.bump_topic()

            if last_dsa_check is None or time.time() - last_dsa_check > 60 * dsa_freq:
                last_dsa_check = time.time()

                for line in debian_security.get_new_dsas():
                    bot.say('#rebuild', line)

                # After a successful fetch, reset the exception count
                exception_count = 0
                # After a successful fetch, we reset timer to 5m
                dsa_freq = DSA_FREQ_DEFAULT
        except Exception as ex:
            exception_count += 1
            error_msg = f'ircbot exception in timer: {ex}, this error occurred {exception_count} times.'
            if exception_count > 9:
                bot.say('#rebuild', error_msg)
            bot.handle_error(
                dedent(
                    """
                {error}

                {traceback}
                """,
                ).format(
                    error=error_msg,
                    traceback=format_exc(),
                ),
            )
            dsa_freq = min(dsa_freq + DSA_FREQ_BACKOFF, DSA_FREQ_MAX)

        time.sleep(1)
