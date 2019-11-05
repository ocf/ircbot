"""Provides a basic Flask server to handle webhooks and help information"""
from __future__ import annotations

import collections
import os
from types import ModuleType
from typing import DefaultDict
from typing import List
from typing import Set
from typing import Tuple
from typing import TYPE_CHECKING

from flask import Flask
from flask import render_template
from flask import request

if TYPE_CHECKING:
    from ircbot.ircbot import Listener

app = Flask(__name__)

# Bot plugins, needed for the / route
bot_plugins: List[Tuple[ModuleType, Set[Listener]]] = []


def register(bot):
    bot.add_thread(start_server)


@app.route('/', methods=['GET'])
def route_base():
    global bot_plugins

    if not bot_plugins:
        # Compute and cache the bot's plugins
        bot_plugin_set: DefaultDict[ModuleType, Set[Listener]] = collections.defaultdict(set)
        for listener in app.bot.listeners:
            bot_plugin_set[app.bot.plugins[listener.plugin_name]].add(listener)

        bot_plugins = sorted(bot_plugin_set.items(), key=lambda p: p[0].__name__)

    return render_template(
        'help.html',
        plugins=bot_plugins,
    )


@app.route('/macros', methods=['GET'])
def route_macros():
    return render_template(
        'macros.html',
        macros=app.bot.plugins['macros'].list(app.bot),
    )


@app.route('/hook/prometheus', methods=['POST'])
def route_prometheus():
    body_json = request.get_json()
    for alert in body_json['alerts']:
        if alert['status'] == 'resolved':
            status = '\x02\x0303OK\x0F'
        else:
            status = '\x02\x0304FIRING\x0F'

        alert = '{status} \x02{alertname}\x0F: {summary}'.format(
            status=status,
            alertname=alert['labels']['alertname'],
            summary=alert['annotations']['summary'],
        )
        app.bot.say('#rebuild-spam', alert)

    return ('', 204)


def start_server(bot):
    port = os.getenv('HTTP_PORT', 8888)
    app.bot = bot
    app.run(host='0.0.0.0', port=int(port))
