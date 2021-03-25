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

COPY ./kafka_certs /app/kafka_certs
COPY ./common /app/common
COPY ./monitor /app/monitor
# COPY ./monitor/requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip
RUN python -m pip install -r monitor/requirements.txt --no-cache-dir

ENV PYTHONPATH /app
ENV PYTHONUNBUFFERED 1

# ENV SPIDER_NAME websites_metrics
ENV SCRAPY_SETTINGS_MODULE=monitor.monitor.settings

# chmod +x /app/monitor/monitor/init.sh
# ENTRYPOINT [ "/app/monitor/monitor/init.sh" ]

# ADD ./monitor/init.sh /init.sh
# RUN ["chmod", "+x", "/app/monitor/init.sh"]

# RUN ["cd" "/app/monitor"]
ENTRYPOINT ["/app/monitor/init.sh"]
