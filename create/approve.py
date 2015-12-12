#!/usr/bin/env python3
import sys
import time
from argparse import ArgumentParser
from configparser import ConfigParser
from textwrap import dedent

import yaml
from celery import Celery
from ocflib.account.creation import encrypt_password
from ocflib.account.creation import NewAccountRequest
from ocflib.account.submission import get_tasks
from ocflib.account.submission import NewAccountResponse
from ocflib.account.validators import validate_password
from ocflib.misc.shell import bold
from ocflib.misc.shell import edit_file
from ocflib.misc.shell import green
from ocflib.misc.shell import prompt_for_new_password
from ocflib.misc.shell import red
from ocflib.misc.shell import yellow
from ocflib.ucb.groups import group_by_oid

TEMPLATE = dedent(
    """\
    user_name:
    group_name: {group_name}
    callink_oid: {callink_oid}
    signatory:
    email: {email}

    # Please ensure that:
    #  * Person requesting account is signatory of group
    #    - Look up the signatory's CalNet UID on directory.berkeley.edu
    #    - Use `signat <uid>` to list groups they are a signatory for
    #  * Group does not have existing account (use checkacct)
    #  * Requested account name is based on group name
    #
    # vim: ft=yaml
    """
)


def wait_for_task(celery, task):
    """Wait for a validate_then_create_account task."""
    print('Waiting...', end='')
    task.wait()  # this should be almost instant

    if isinstance(task.result, NewAccountResponse):
        print()
        return task.result

    task = celery.AsyncResult(task.result)

    last_status_len = 0
    while not task.ready():
        time.sleep(0.25)

        meta = task.info
        if isinstance(meta, dict) and 'status' in meta:
            status = meta['status']
            if len(status) > last_status_len:
                for line in status[last_status_len:]:
                    print()
                    print(line, end='')

                last_status_len = len(status)

        print('.', end='')
        sys.stdout.flush()
    print()
    if isinstance(task.result, Exception):
        raise task.result
    else:
        return task.result


def main():
    def_group_name = ''
    def_callink_oid = ''
    def_email = ''

    parser = ArgumentParser(description='Create new OCF group accounts.')
    parser.add_argument('oid', type=int, nargs='?', help='CalLink OID for the group.')
    args = parser.parse_args()

    if args.oid:
        group = group_by_oid(args.oid)
        if not group:
            print(red('No group with OID {}').format(args.oid))
            return
        if group['accounts']:
            print(yellow(
                'Warning: there is an existing group account with OID {}: {}'.format(
                    args.oid,
                    ', '.join(group['accounts']),
                ),
            ))
            input('Press any key to continue...')
        def_group_name = group['name']
        def_callink_oid = args.oid
        def_email = group['email']

    content = TEMPLATE.format(
        group_name=def_group_name,
        callink_oid=def_callink_oid,
        email=def_email
    )

    while True:
        content = edit_file(content)
        try:
            account = yaml.safe_load(content)
        except yaml.YAMLError as ex:
            print('Error parsing your YAML:')
            print(ex)
            input('Press enter to continue...')
            continue

        missing_key = False
        for key in ['user_name', 'group_name', 'callink_oid', 'email']:
            if account.get(key) is None:
                print('Missing value for key: ' + key)
                missing_key = True
        if missing_key:
            input('Press enter to continue...')
            continue

        try:
            password = prompt_for_new_password(
                validator=lambda pwd: validate_password(
                    account['user_name'], pwd),
            )
        except KeyboardInterrupt:
            # we want to allow cancelling during the "enter password" stage
            # without completely exiting approve
            print()
            input('Press enter to start over (or ^C again to cancel)...')
            continue

        request = NewAccountRequest(
            user_name=account['user_name'],
            real_name=account['group_name'],
            is_group=True,
            calnet_uid=None,
            callink_oid=account['callink_oid'],
            email=account['email'],
            encrypted_password=encrypt_password(
                password,
                '/etc/ocf-create/create.pub',
            ),
            handle_warnings=NewAccountRequest.WARNINGS_WARN,
        )

        print()
        print(bold('Pending account request:'))
        print(dedent(
            """\
            User Name: {request.user_name}
            Group Name: {request.real_name}
            CalLink OID: {request.callink_oid}
            Email: {request.email}
            """
        ).format(request=request))

        if input('Submit request? [yN] ') != 'y':
            input('Press enter to continue.')
            continue

        conf = ConfigParser()
        conf.read('/etc/ocf-create/ocf-create.conf')

        celery = Celery(
            broker=conf.get('celery', 'broker'),
            backend=conf.get('celery', 'backend'),
        )
        tasks = get_tasks(celery)
        task = tasks.validate_then_create_account.delay(request)

        response = wait_for_task(celery, task)
        new_request = None

        if response.status == NewAccountResponse.REJECTED:
            print(bold(red(
                'Account requested was rejected for the following reasons:'
            )))
            for error in response.errors:
                print(red('  - {}'.format(error)))
            input('Press enter to start over (or ^C to cancel)...')
            continue
        elif response.status == NewAccountResponse.FLAGGED:
            print(bold(yellow(
                'Account requested was flagged for the following reasons:'
            )))
            for error in response.errors:
                print(yellow('  - {}'.format(error)))
            print(bold(
                'You can either create the account anyway, or go back and '
                'modify the request.'
            ))
            choice = input('Create the account anyway? [yN] ')

            if choice in ('y', 'Y'):
                new_request = request._replace(
                    handle_warnings=NewAccountRequest.WARNINGS_CREATE,
                )
                task = tasks.validate_then_create_account.delay(new_request)
                response = wait_for_task(celery, task)
            else:
                input('Starting over, press enter to continue...')
                continue

        if response.status == NewAccountResponse.CREATED:
            print(bold(green('Account created!')))
            print('Your account was created successfully.')
            print('You\'ve been sent an email with more information.')
            return
        else:
            # this shouldn't be possible; we must have entered some weird state
            # TODO: report via ocflib
            print(bold(red('Error: Entered unexpected state.')))
            print(red('The request we submitted was:'))
            print(red(request))
            print(red('The new request we submitted (if any) was:'))
            print(red(new_request))
            print(red('The response we received was:'))
            print(red(response))
            print(bold(red('Not really sure what to do here, sorry.')))
            input('Press enter to start over...')


if __name__ == '__main__':
    main()
