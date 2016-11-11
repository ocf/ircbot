import requests


def _get_overview(api_key):
    req = requests.post(
        'https://identity.api.rackspacecloud.com/v2.0/tokens',
        json={
            'auth': {
                'RAX-KSKEY:apiKeyCredentials': {
                    'username': 'theocf',
                    'apiKey': api_key,
                },
            },
        }
    )
    assert req.status_code == 200, req.status_code
    j = req.json()
    token_id = j['access']['token']['id']

    service, = [
        service
        for service in j['access']['serviceCatalog']
        if service['type'] == 'rax:monitor'
    ]
    public_url = service['endpoints'][0]['publicURL']

    req = requests.get(
        public_url + '/views/overview',
        headers={
            'X-Auth-Token': token_id,
        },
    )
    assert req.status_code == 200, req.status_code
    j = req.json()

    ok_entities = set()
    bad_entities = {}

    for entity in j['values']:
        entity_name = entity['entity']['label']
        bad_checks = {}

        for check in entity['checks']:
            check_name = check['label']
            alarms_for_check = [
                alarm for alarm in entity['alarms']
                if alarm['check_id'] == check['id']
            ]
            alarms_with_state = [
                (
                    alarm,
                    [
                        state
                        for state in entity['latest_alarm_states']
                        if state['alarm_id'] == alarm['id']
                    ][0],
                )
                for alarm in alarms_for_check
            ]
            bad_alarms = [
                (alarm['label'], state['state'])
                for alarm, state in alarms_with_state
                if state['state'] != 'OK'
            ]

            if bad_alarms:
                bad_checks[check_name] = bad_alarms

        if bad_checks:
            bad_entities[entity_name] = bad_checks
        else:
            ok_entities.add(entity_name)

    return ok_entities, bad_entities


def get_summary(api_key):
    ok_entities, bad_entities = _get_overview(api_key)
    color = '\x02\x03'
    if bad_entities:
        color += '04'
    else:
        color += '03'

    text = '{}{}/{} entities OK'.format(
        color,
        len(ok_entities),
        len(ok_entities) + len(bad_entities),
    )

    if bad_entities:
        text += '; bad entities: '
        text += ', '.join(
            '{} ({})'.format(
                entity_name,
                ', '.join(
                    '{} is {}'.format(alarm, status)
                    for alarm, status in alarms.items()
                )
            )
            for entity_name, alarms in bad_entities.items()
        )

    return text
