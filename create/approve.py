#!/usr/bin/env python3
import sys
import time
from argparse import ArgumentParser
from configparser import ConfigParser
from textwrap import dedent

import yaml
from celery import Celery
from Crypto.PublicKey import RSA
from ocflib.account.creation import encrypt_password
from ocflib.account.creation import NewAccountRequest
from ocflib.account.submission import get_tasks
from ocflib.account.submission import NewAccountResponse
from ocflib.account.validators import validate_password
from ocflib.constants import CREATE_PUBLIC_KEY
from ocflib.misc.mail import send_problem_report
from ocflib.misc.shell import bold
from ocflib.misc.shell import edit_file
from ocflib.misc.shell import green
from ocflib.misc.shell import prompt_for_new_password
from ocflib.misc.shell import red
from ocflib.misc.shell import yellow
from ocflib.ucb.groups import group_by_oid

TEMPLATE = dedent(
    # "\n\" is to hack around linters complaining about trailing whitespace
    """\
    user_name: \n\
    group_name: {group_name}
    callink_oid: {callink_oid}
    signatory: \n\
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


def get_group_information(group_oid):
    """Returns tuple (group name, group oid, group email)."""
    if group_oid:
        group = group_by_oid(group_oid)

        if not group:
            print(red('No group with OID {}').format(group_oid))
            sys.exit(1)

        if group['accounts']:
            print(yellow(
                'Warning: there is an existing group account with OID {}: {}'.format(
                    group_oid,
                    ', '.join(group['accounts']),
                ),
            ))
            input('Press enter to continue...')

        return (group['name'], group_oid, group['email'])
    else:
        return ('', '', '')


def make_account_request(account, password):
    request = NewAccountRequest(
        user_name=account['user_name'],
        real_name=account['group_name'],
        is_group=True,
        calnet_uid=None,
        callink_oid=account['callink_oid'],
        email=account['email'],
        encrypted_password=encrypt_password(
            password,
            RSA.importKey(CREATE_PUBLIC_KEY),
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

    return request


def create_account(request):
    """Returns tuple (tasks queue, celery connection, task reponse)."""
    conf = ConfigParser()
    conf.read('/etc/ocf-create/ocf-create.conf')

    celery = Celery(
        broker=conf.get('celery', 'broker'),
        backend=conf.get('celery', 'backend'),
    )
    tasks = get_tasks(celery)
    task = tasks.validate_then_create_account.delay(request)

    response = wait_for_task(celery, task)

    return (tasks, celery, response)


def error_report(request, new_request, response):
    print(bold(red('Error: Entered unexpected state.')))
    print(bold('An email has been sent to OCF staff'))

    error_report = dedent(
        """\
        Error encountered running approve!

        The request we submitted was:
        {request}

        The request we submitted after being flagged (if any) was:
        {new_request}

        The response we received was:
        {response}
        """
    ).format(
        request=request,
        new_request=new_request,
        reponse=response
    )

    send_problem_report(error_report)


def main():
    def pause_error_msg():
        input('Press enter to edit group information (or Ctrl-C to exit)...')

    parser = ArgumentParser(description='Create new OCF group accounts.')
    parser.add_argument('oid', type=int, nargs='?', help='CalLink OID for the group.')
    args = parser.parse_args()

    group_name, callink_oid, email = get_group_information(args.oid)

    content = TEMPLATE.format(
        group_name=group_name,
        callink_oid=callink_oid,
        email=email
    )

    while True:
        content = edit_file(content)
        try:
            account = yaml.safe_load(content)
        except yaml.YAMLError as ex:
            print('Error parsing your YAML:')
            print(ex)
            pause_error_msg()
            continue

        missing_key = False
        for key in ['user_name', 'group_name', 'callink_oid', 'email']:
            if account.get(key) is None:
                print('Missing value for key: ' + key)
                missing_key = True
        if missing_key:
            pause_error_msg()
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
            pause_error_msg()
            continue

        request = make_account_request(account, password)

        if input('Submit request? [yN] ') not in ('y', 'Y'):
            pause_error_msg()
            continue

        tasks, celery, response = create_account(request)
        new_request = None

        if response.status == NewAccountResponse.REJECTED:
            print(bold(red(
                'Account requested was rejected for the following reasons:'
            )))
            for error in response.errors:
                print(red('  - {}'.format(error)))

            pause_error_msg()
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
                pause_error_msg()
                continue

        if response.status == NewAccountResponse.CREATED:
            print(bold(green('Account created!')))
            print('Your account was created successfully.')
            print('You\'ve been sent an email with more information.')
            return
        else:
            # this shouldn't be possible; we must have entered some weird state
            error_report(request, new_request, response)
            pause_error_msg()


if __name__ == '__main__':
    main()
