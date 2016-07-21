"""Celery worker entrypoint.

This module is not intended to be imported directly, but instead to be used as
the `-A` argument to the celery worker.

The create-worker script will handle reading settings from files, setting
appropriate environment variables, and exec-ing celery. It is the recommended
way to use create.
"""
import os
from configparser import ConfigParser
from textwrap import dedent
from traceback import format_exc

from celery import Celery
from celery.signals import setup_logging
from ocflib.account.submission import AccountCreationCredentials
from ocflib.account.submission import get_tasks
from ocflib.misc.mail import send_problem_report

conf = ConfigParser()
conf.read(os.environ['CREATE_CONFIG_FILE'])

celery = Celery(
    broker=conf.get('celery', 'broker'),
    backend=conf.get('celery', 'backend'),
)

creds = AccountCreationCredentials(**{
    field:
        conf.get(*field.split('_'))
        for field in AccountCreationCredentials._fields
})

# if in debug mode, disable celery logging so that stdin / stdout / stderr
# don't get tampered with (otherwise, interactive debuggers won't work)
if os.environ.get('CREATE_DEBUG', ''):
    # pylint: disable=unused-argument
    def no_logging(*args, **kwargs):
        pass
    setup_logging.connect(no_logging)


def failure_handler(exc, task_id, args, kwargs, einfo):
    """Handle errors in Celery tasks by reporting via ocflib.

    We want to report actual errors, not just validation errors. Unfortunately
    it's hard to pick them out. For now, we just ignore ValueErrors and report
    everything else.

    It's likely that we'll need to revisit that some time in the future.
    """
    if isinstance(exc, ValueError):
        return

    try:
        send_problem_report(dedent(
            """\
            An exception occured in create:

            {traceback}

            Task Details:
              * task_id: {task_id}

            Try `journalctl -u ocf-create` for more details."""
        ).format(
            traceback=einfo,
            task_id=task_id,
            args=args,
            kwargs=kwargs,
            einfo=einfo,
        ))
    except Exception as ex:
        print(ex)  # just in case it errors again here
        send_problem_report(dedent(
            """\
            An exception occured in create, but we errored trying to report it:

            {traceback}
            """
        ).format(traceback=format_exc()))
        raise


tasks = get_tasks(celery, credentials=creds)
for task in tasks:
    locals()[task.__name__] = task
    task.on_failure = failure_handler
