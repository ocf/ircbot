# create
[![Build Status](https://jenkins.ocf.berkeley.edu/buildStatus/icon?job=create-test)](https://jenkins.ocf.berkeley.edu/view/create-test/)
[![Code Health](https://landscape.io/github/ocf/create/master/landscape.svg?style=flat)](https://landscape.io/github/ocf/create/master)

Celery worker and IRC bot for account creation

## Development

Clone the repo, and run `make venv` inside the repository directory. This will
install the required python packages needed to run create.

The worker and bot are run in production as separate systemd services, but for
development you probably want to just run them manually using the commands
explained below. Be aware that the IRC bot won't connect if another instance
is already connected, so you may need to stop the production version with
`systemctl stop ocf-create-irc` if you are trying to get the IRC bot to run.
The same applies with the celery worker, but it still at least connects when
another celery instance is running.

To run the bot, first you must be on supernova, since the credentials are only
accessible from there. Then, after installing the packages required, source the
virtualenv (`source .activate.sh`) to enable the commands to use for running
the celery worker and IRC bot. To automatically source and unsource the
virtualenv when entering/leaving the directory, try using
[aactivator](https://github.com/Yelp/aactivator).

To start the IRC bot, just run `create-ircbot`, and to start the celery worker,
run `create-worker`. The bot and celery worker will by default use the config
file already on supernova, but you can specify your own config file to use for
development with the `-c` or `--config` parameter to either one. More help is
available with `-h` or `--help`. To exit the virtualenv when you are done
working on create, just type `deactivate`.
