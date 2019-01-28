"""Provide help information."""
import collections
import http.server
import os
import threading

import jinja2


def register(bot):
    threading.Thread(target=help_server, args=(bot,), daemon=True).start()
    bot.listen(r'^help$', help, require_mention=True)
    bot.listen(r'^macros$', help_macro, require_mention=True)


def help(bot, msg):
    """Provide a link to this help page."""
    msg.respond('https://ircbot.ocf.berkeley.edu/')


def help_macro(bot, msg):
    """Provide a link to the list of macros."""
    msg.respond('https://ircbot.ocf.berkeley.edu/macros')


def help_shorturl(bot, msg):
    """Provide a link to the list of shorturls."""
    msg.respond('https://ircbot.ocf.berkeley.edu/shorturls')


def build_request_handler(bot):
    jinja_env = jinja2.Environment(
        loader=jinja2.PackageLoader('ircbot', ''),
        autoescape=True,
    )

    class RequestHandler(http.server.BaseHTTPRequestHandler):

        def render_response(self, template, **context):
            rendered = jinja_env.get_template(template).render(**context).encode('utf-8')
            self.send_response(200, 'Okay')
            self.send_header('Content-Length', len(rendered))
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(rendered)

        def render_404(self):
            self.send_response(404, 'File not found')
            self.end_headers()
            self.wfile.write(b'404 File not found')

        def do_GET(self):
            if self.path == '/':
                plugins = collections.defaultdict(set)
                for listener in bot.listeners:
                    plugins[bot.plugins[listener.plugin_name]].add(listener)

                self.render_response(
                    'plugin/templates/help.html',
                    plugins=sorted(plugins.items(), key=lambda p: p[0].__name__),
                )
            elif self.path == '/macros':
                self.render_response(
                    'plugin/templates/macros.html',
                    macros=bot.plugins['macros'].list(bot),
                )
            elif self.path.startswith('/shorturls'):
                query_items = self.path.lstrip('/').split('/')

                if not query_items[1]:
                    self.render_response(
                        'plugin/templates/shorturls.html',
                        shorturls=bot.plugins['shorturls'].list(bot),
                    )
                else:
                    candidate_target = bot.plugins['shorturls'].retrieve(bot, '/'.join(query_items[1:]))

                    if candidate_target:
                        self.send_response(302, 'Found')
                        self.send_header('Content-Length', 0)
                        self.send_header('Location', candidate_target)
                        self.end_headers()
                    else:
                        self.render_404()
            else:
                self.render_404()

    return RequestHandler


def help_server(bot):
    port = os.getenv('HTTP_PORT', 8888)
    server = http.server.HTTPServer(('0.0.0.0', int(port)), build_request_handler(bot))
    server.serve_forever()
