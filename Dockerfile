FROM python:3.10.2-alpine3.15

USER root

WORKDIR /opt/trading

ADD . /opt/trading/.

RUN python3 -m pip install -r requirements.txt