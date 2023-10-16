from pathlib import Path

from transpire.resources import Deployment
from transpire.resources import Ingress
from transpire.resources import Secret
from transpire.resources import Service
from transpire.types import Image
from transpire.utils import get_image_tag

name = 'ircbot'


def objects():
    dep = Deployment(
        name='ircbot',
        image=get_image_tag('ircbot'),
        ports=[8888],
    )

    dep.obj.spec.template.spec.volumes = [
        {
            'name': 'secrets',
            'secret': {'secretName': ircbot},
        },
    ]

    dep.obj.spec.template.spec.containers[0].volume_mounts = [
        {
            'name': 'secrets',
            'mountPath': '/etc/ocf-ircbot',
        },
    ]

    svc = Service(
        name='ircbot',
        selector=dep.get_selector(),
        port_on_pod=8888,
        port_on_svc=80,
    )

    ing = Ingress.from_svc(
        svc=svc,
        host='ircbot.ocf.berkeley.edu',
        path_prefix='/',
    )

    yield Secret(
        name='ircbot',
        string_data={
            'create-redis.key': '',
            'ocf-ircbot.conf': '',
        },
    ).build()

    yield dep.build()
    yield svc.build()
    yield ing.build()


def images():
    yield Image(name='ircbot', path=Path('/'))
