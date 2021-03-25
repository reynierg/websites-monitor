"""Scrapy settings for monitor project

For simplicity, this file contains only settings considered important or
commonly used. You can find more settings consulting the documentation:

    https://docs.scrapy.org/en/latest/topics/settings.html
    https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
    https://docs.scrapy.org/en/latest/topics/spider-middleware.html
"""

import inspect
import os
import types
import typing

from dotenv import load_dotenv


load_dotenv(verbose=True, override=True)

MONITOR_BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(inspect.getfile(
        typing.cast(
            types.FrameType,
            inspect.currentframe()
        )
    )))
)

BOT_NAME = "monitor"

# SPIDER_MODULES = ['monitor.spiders']
# NEWSPIDER_MODULE = 'monitor.spiders'
SPIDER_MODULES = ["monitor.monitor.spiders"]
NEWSPIDER_MODULE = "monitor.monitor.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'monitor (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = os.getenv("TELNETCONSOLE_ENABLED", "0") == "1"

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'monitor.middlewares.MonitorSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'monitor.middlewares.MonitorDownloaderMiddleware': 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    # 'monitor.pipelines.MonitorPipeline': 300,
    "monitor.monitor.pipelines.MonitorPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#
# httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# File name to use for logging output. If None, standard error will be used.
LOG_FILE = f"{MONITOR_BASE_DIR}{os.sep}data{os.sep}logs.log"

# Minimum level to log. Available levels are: CRITICAL, ERROR, WARNING, INFO, DEBUG.
# For more info see Logging.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Disable retry. We just want to know if the web site is reachable or not, in the
# first try:
RETRY_ENABLED = False

# Whether the Redirect middleware will be enabled.
REDIRECT_ENABLED = not os.getenv("REDIRECT_ENABLED", "0") == "0"

# The maximum number of redirections that will be followed for a single request.
# After this maximum, the request’s response is returned as is.
REDIRECT_MAX_TIMES = (
    0
    if os.getenv("REDIRECT_MAX_TIMES", "0") == "0" or not os.getenv(
        "REDIRECT_MAX_TIMES", "0").isdigit()
    else int(typing.cast(str, os.getenv("REDIRECT_MAX_TIMES")))
)

# Timeout for processing of DNS queries in seconds.
DNS_TIMEOUT = int(os.getenv("DNS_TIMEOUT", "60"))

# The amount of time (in secs) that the downloader will wait before timing out.
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "180"))


# ############ CUSTOM SETTINGS #############
class CustomSettings:
    """Defines custom settings"""

    # Urls provider: Supported providers: CsvUrlsProvider, JsonUrlsProvider.
    URLS_PROVIDER_TYPE = os.getenv("URLS_PROVIDER_TYPE", "CsvUrlsProvider")

    # File from where the urls should be parsed.
    URLS_SRC = f"{MONITOR_BASE_DIR}{os.sep}data{os.sep}urls." + (
        "csv" if URLS_PROVIDER_TYPE == "CsvUrlsProvider" else "json"
    )

    STREAM_PRODUCER_TYPE = os.getenv("STREAM_PRODUCER_TYPE", "KafkaStreamProducer")


CUSTOM_SETTINGS = CustomSettings()
