FROM docker.ocf.berkeley.edu/theocf/debian:stretch

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential \
        cracklib-runtime \
        libcrack2-dev \
        libffi-dev \
        libssl-dev \
        python3 \
        python3-dev \
        python3-pip \
        redis-tools \
        runit \
        virtualenv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN install -d --owner=nobody /opt/ircbot /opt/ircbot/venv

COPY requirements.txt /opt/ircbot/
RUN virtualenv -ppython3 /opt/ircbot/venv \
    && /opt/ircbot/venv/bin/pip install pip==8.1.2 \
    && /opt/ircbot/venv/bin/pip install \
        -r /opt/ircbot/requirements.txt

COPY ircbot /opt/ircbot/ircbot

COPY services /opt/ircbot/services
RUN chown -R nobody:nogroup /opt/ircbot
USER nobody

WORKDIR /opt/ircbot

CMD ["runsvdir", "/opt/ircbot/services"]
