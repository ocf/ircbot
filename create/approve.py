#!/usr/bin/env python3
from configparser import ConfigParser
from textwrap import dedent

import yaml
from celery import Celery
from ocflib.account.creation import encrypt_password
from ocflib.account.submission import get_tasks
from ocflib.account.submission import NewAccountRequest
from ocflib.account.validators import validate_password
from ocflib.misc.shell import bold
from ocflib.misc.shell import edit_file
from ocflib.misc.shell import prompt_for_new_password

TEMPLATE = dedent(
    """\
    user_name:
    group_name:
    callink_oid:
    account_name:
    signatory:
    email:

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


def main():
    content = TEMPLATE

    while True:
        content = edit_file(content)
        try:
            account = yaml.safe_load(content)
        except yaml.YAMLError as ex:
            print('Error parsing your YAML:')
            print(ex)
            input('Press enter to continue...')
            continue

        password = prompt_for_new_password(
            validator=lambda pwd: validate_password(account['user_name'], pwd),
        )

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

        if input(bold('Submit request? [yN] ')) != 'y':
            input('Press enter to continue.')
            continue

        conf = ConfigParser()
        conf.read('/etc/ocf-create/ocf-create.conf')

        celery = Celery(
            broker=conf.get('celery', 'broker'),
            backend=conf.get('celery', 'backend'),
        )
        tasks = get_tasks(celery)
        tasks.create_account.delay(request)


if __name__ == '__main__':
    main()
