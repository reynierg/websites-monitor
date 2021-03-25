#!/bin/bash

while true; do
        #scrapy crawl $SPIDER_NAME
        python3 /app/monitor/monitor/spiders/websites_metrics_spider.py
        sleep ${WEBSITES_CHECK_INTERVAL:-60}
done
