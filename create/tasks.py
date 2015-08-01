"""Celery worker entrypoint.

This module is not intended to be imported directly, but instead to be used as
the `-A` argument to the celery worker.

The create-worker script will handle reading settings from files, setting
appropriate environment variables, and exec-ing celery. It is the recommended
way to use create.
"""
import os

from celery import Celery
from ocflib.account.submission import get_tasks


celery = Celery(
    broker=os.environ['CREATE_CELERY_BROKER'],
    backend=os.environ['CREATE_CELERY_BACKEND'],
)
for task in get_tasks(celery):
    locals()[task.__name__] = task
