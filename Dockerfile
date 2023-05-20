FROM docker.ocf.berkeley.edu/theocf/debian:bullseye

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential \
        cracklib-runtime \
        libcrack2-dev \
        libffi-dev \
        libssl-dev \
        python3-dev \
        redis-tools \
        virtualenv \
        rustc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN install -d --owner=nobody /opt/ircbot /opt/ircbot/venv

COPY requirements.txt /opt/ircbot/
RUN virtualenv -ppython3.9 /opt/ircbot/venv \
    && /opt/ircbot/venv/bin/pip install \
        -r /opt/ircbot/requirements.txt

COPY ircbot /opt/ircbot/ircbot

RUN chown -R nobody:nogroup /opt/ircbot
USER nobody

WORKDIR /opt/ircbot

CMD ["/opt/ircbot/venv/bin/python", "-m", "ircbot.ircbot"]
