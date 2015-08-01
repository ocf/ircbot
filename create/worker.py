#!/usr/bin/env python3
"""Celery worker wrapper.

Reads options from a config file (or command-line arguments), then execs a
celery worker process.
"""
import argparse
import os

import yaml


def main():
    """Entrypoint into wrapper."""
    parser = argparse.ArgumentParser(
        description='Process incoming OCF account creation requests.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--broker',
        type=str,
        help='Broker URI to use for Celery.',
    )
    parser.add_argument(
        '--backend',
        type=str,
        help='Backend URI to use for Celery.',
    )
    parser.add_argument(
        '-l',
        '--log-level',
        type=str,
        default='info',
        help='Backend URI to use for Celery.',
    )
    parser.add_argument(
        '-c',
        '--config',
        type=str,
        default='/etc/ocf-create/config.yaml',
        help='Config file to read from.',
    )
    args = parser.parse_args()

    broker, backend = args.broker, args.backend
    if not broker or not backend:
        with open(args.config) as f:
            config = yaml.safe_load(f)

            broker = broker or config.broker
            backend = backend or config.backend

    os.environ['CREATE_CELERY_BROKER'] = broker
    os.environ['CREATE_CELERY_BACKEND'] = backend
    os.execvp(
        'celery',
        (
            'celery',
            'worker',
            '-A', 'create.tasks',
            '-l', args.log_level,
        ),
    )


if __name__ == '__main__':
    main()
