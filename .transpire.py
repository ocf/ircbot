from pathlib import Path

from transpire.resources import Deployment, Ingress, Secret, Service
from transpire.types import Image
from transpire.utils import get_image_tag, get_revision

name = "ircbot"
auto_sync = True

def dep_patches(dep):
    dep.obj.spec.template.spec.dns_policy = "ClusterFirst"
    dep.obj.spec.template.spec.dns_config = {"searches": ["ocf.berkeley.edu"]}

    dep.obj.spec.template.spec.volumes = [
        {"name": "config", "secret": {"secretName": "ircbot"}},
    ]

    dep.obj.spec.template.spec.containers[0].volume_mounts = [
        {"name": "config", "mountPath": "/etc/ocf-ircbot"},
    ]


def images():
    yield Image(name="ircbot", path=Path("/"))


def objects():
    secret = Secret(
        name="ircbot",
        string_data={
            "ocf-ircbot.conf": "",
        },
    )
    yield secret.build()

    dep_bot = Deployment(
        name=name,
        image=get_image_tag("ircbot"),
        ports=[8888],
    )
    # TODO: Switch this to .patch() API.
    dep_patches(dep_bot)
    yield dep_bot.build()

    svc_bot = Service(
        name=name,
        selector=dep_bot.get_selector(),
        port_on_pod=8888,
        port_on_svc=80,
    )
    yield svc_bot.build()

    ing_bot = Ingress.from_svc(
        svc=svc_bot,
        host="ircbot.ocf.berkeley.edu",
        path_prefix="/",
    )
    yield ing_bot.build()