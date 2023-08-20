FROM docker.ocf.berkeley.edu/theocf/debian:bullseye-py

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential \
        cracklib-runtime \
        libcrack2-dev \
        libffi-dev \
        libssl-dev \
        redis-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install virtualenv

RUN install -d --owner=nobody /opt/ircbot /opt/ircbot/venv

COPY requirements.txt /opt/ircbot/
RUN virtualenv -ppython3.7 /opt/ircbot/venv \
    && /opt/ircbot/venv/bin/pip install \
        -r /opt/ircbot/requirements.txt

COPY ircbot /opt/ircbot/ircbot

RUN chown -R nobody:nogroup /opt/ircbot
USER nobody

WORKDIR /opt/ircbot

CMD ["/opt/ircbot/venv/bin/python", "-m", "ircbot.ircbot"]
