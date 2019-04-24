ARG FROM=python:3.6
FROM ${FROM}

LABEL org.opencontainers.image.authors='airship-discuss@lists.airshipit.org, irc://#airshipit@freenode'
LABEL org.opencontainers.image.url='https://airshipit.org'
LABEL org.opencontainers.image.documentation='https://airship-spyglass.readthedocs.org'
LABEL org.opencontainers.image.source='https://opendev.org/airship/spyglass'
LABEL org.opencontainers.image.vendor='The Airship Authors'
LABEL org.opencontainers.image.licenses='Apache-2.0'

VOLUME /var/spyglass
WORKDIR /var/spyglass


COPY requirements.txt /opt/spyglass/requirements.txt
RUN pip3 install --no-cache-dir -r /opt/spyglass/requirements.txt

COPY . /opt/spyglass
RUN pip3 install -e /opt/spyglass
