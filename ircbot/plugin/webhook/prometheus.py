"""Handle webhooks from Prometheus AlertManager"""
# See https://prometheus.io/docs/alerting/configuration/#webhook_config for a
# description of the webhook format.

import json

PATH = 'prometheus'

def handle_hook(bot, body):
    body_json = json.loads(body.decode())
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
        bot.say('#rebuild-spam', alert)
