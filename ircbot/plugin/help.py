"""Provide help information."""
import collections
import http.server
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

        def do_GET(self):
            if self.path == '/':
                plugins = collections.defaultdict(set)
                for listener in bot.listeners:
                    plugins[bot.plugins[listener.fn.__module__]].add(listener)
                self.render_response(
                    'plugin/templates/help.html',
                    plugins=sorted(plugins.items(), key=lambda p: p[0].__name__),
                )
            elif self.path == '/macros':
                self.render_response(
                    'plugin/templates/macros.html',
                    macros=bot.plugins['macros'].list(bot),
                )
            else:
                self.send_response(404, 'File not found')
                self.end_headers()
                self.wfile.write(b'404 File not found')

    return RequestHandler


def help_server(bot):
    server = http.server.HTTPServer(('0.0.0.0', 8888), build_request_handler(bot))
    server.serve_forever()
