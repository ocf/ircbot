ircbot
======

[![Build Status](https://jenkins.ocf.berkeley.edu/buildStatus/icon?job=ircbot/master)](https://jenkins.ocf.berkeley.edu/job/ircbot/job/master/)

IRC bot for account creation and other things.

Running
-------

Running `make dev` will have your bot join the `#test` channel on Slack/IRC
with the username `create-${username}`.

An empty configuration is provided in `ocf-ircbot.conf.example`. The production
configuration is located at `/opt/puppetlabs/shares/private/docker/ircbot`
on the Puppet master.
