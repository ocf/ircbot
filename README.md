ircbot
======

[![Build Status](https://jenkins.ocf.berkeley.edu/buildStatus/icon?job=ocf/ircbot/master)](https://jenkins.ocf.berkeley.edu/job/ocf/job/ircbotjob/master/)

IRC bot for account creation and other things.

## Working on `ircbot`

We recommend working on `supernova`, the staff login server. `supernova` has
all of the configuration files and libraries necessary to run `ircbot`. See our
[instructions for logging into
supernova](https://www.ocf.berkeley.edu/docs/staff/procedures/ssh-supernova/).

```
$ git clone https://github.com/ocf/ircbot.git
$ make install-hooks
```

Once you've made changes, you can run `make dev` to run the bot in testing mode.
In this mode, the bot will join `#yourusername` on IRC. Your username's channel
probably isn't bridged to slack, so you will need to [connect to
IRC](https://www.ocf.berkeley.edu/docs/contact/irc/) to interact with the bot.
