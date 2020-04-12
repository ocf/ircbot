"""Provides a basic Flask server to handle webhooks and help information"""
from __future__ import annotations

import collections
import os
from types import ModuleType
from typing import DefaultDict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import TYPE_CHECKING

import cheroot.wsgi
from flask import abort
from flask import Flask
from flask import render_template

if TYPE_CHECKING:
    from ircbot.ircbot import CreateBot
    from ircbot.ircbot import Listener

app = Flask(__name__)

# Bot plugins, needed for the / route
create_bot: Optional[CreateBot] = None
bot_plugins: List[Tuple[ModuleType, Set[Listener]]] = []


def register(bot):
    bot.add_thread(start_server)


@app.route('/', methods=['GET'])
def route_base():
    global bot_plugins

    if not bot_plugins:
        # Shouldn't happen, the server is started after bot is set
        if create_bot is None:
            abort(500)

        # Satisfy mypy
        bot: CreateBot = create_bot

        # Compute and cache the bot's plugins
        bot_plugin_set: DefaultDict[ModuleType, Set[Listener]] = collections.defaultdict(set)
        for listener in bot.listeners:
            bot_plugin_set[bot.plugins[listener.plugin_name]].add(listener)

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


def start_server(bot):
    global create_bot
    port = int(os.getenv('HTTP_PORT', 8888))
    create_bot = bot
    d = cheroot.wsgi.PathInfoDispatcher({'/': app})
    server = cheroot.wsgi.WSGIServer(('0.0.0.0', port), d)
    server.start()
