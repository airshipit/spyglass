ARG FROM=python:3.6
FROM ${FROM}

VOLUME /var/spyglass
WORKDIR /var/spyglass

ARG ctx_base=.

COPY ${ctx_base}/requirements.txt /opt/spyglass/requirements.txt
RUN pip3 install --no-cache-dir -r /opt/spyglass/requirements.txt

COPY ${ctx_base} /opt/spyglass
RUN pip3 install -e /opt/spyglass
