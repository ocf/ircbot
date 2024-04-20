from pathlib import Path

from transpire.resources import Deployment, Ingress, Secret, Service
from transpire.types import Image
from transpire.utils import get_image_tag, get_revision

name = "ircbot"
auto_sync = True


def images():
    yield Image(name="ircbot", path=Path("/"))


def objects():
    yield Secret(
        name="ircbot",
        string_data={
            "ocf-ircbot.conf": "",
        },
    ).build()

    dep_bot = Deployment(
        name=name,
        image=get_image_tag("ircbot"),
        ports=[8888],
    )
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