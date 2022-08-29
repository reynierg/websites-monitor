FROM python:3.8-slim-buster

RUN apt-get update
RUN apt-get install \
    -y \
    --no-install-recommends \
    gcc \
    libc-dev \
    python3-dev

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

COPY ./monitor/requirements.txt monitor/requirements.txt
RUN python -m pip install --upgrade pip
RUN python -m pip install -r monitor/requirements.txt --no-cache-dir

COPY ./kafka_certs /app/kafka_certs
COPY ./common /app/common
COPY ./monitor /app/monitor

ENV PYTHONPATH /app
ENV PYTHONUNBUFFERED 1

# ENV SPIDER_NAME websites_metrics
ENV SCRAPY_SETTINGS_MODULE=monitor.monitor.settings

ENTRYPOINT ["/app/monitor/init.sh"]
