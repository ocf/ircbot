"""Celery worker entrypoint.

This module is not intended to be imported directly, but instead to be used as
the `-A` argument to the celery worker.

The create-worker script will handle reading settings from files, setting
appropriate environment variables, and exec-ing celery. It is the recommended
way to use create.
"""
import os
from configparser import ConfigParser

from celery import Celery
from celery.signals import setup_logging
from ocflib.account.submission import AccountCreationCredentials
from ocflib.account.submission import get_tasks

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
    def no_logging(*args, **kwargs):
        pass
    setup_logging.connect(no_logging)


tasks = get_tasks(celery, credentials=creds)
for task in tasks:
    locals()[task.__name__] = task
