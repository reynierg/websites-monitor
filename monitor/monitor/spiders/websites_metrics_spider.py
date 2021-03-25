"""Contains logic for the spider to be used for monitor the websites metrics

Also implements the entrypoint to execute the spider.

This file can be imported as a module and contains the following classes and
methods:
    * WebsitesMetricsSpider - Spider to be used to check the state of the
        websites links
    * main - Runs the WebsitesMetricsSpider
"""

import re

import scrapy
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.project import get_project_settings
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TCPTimedOutError
from twisted.internet.error import TimeoutError as TwistedTimeoutError

from monitor.monitor import settings
from monitor.monitor.items import MonitorItem
from monitor.monitor.utils import UrlsProviderFactory
from monitor.monitor.utils import constants


class WebsitesMetricsSpider(scrapy.Spider):
    """Spider to be used to check the state of the websites links

    Methods
    -------
    start_requests()
        Returns an iterable with the Requests to crawl for this spider.
    parse()
        Callback used by Scrapy to process downloaded responses, when
        their requests don't specify a callback.
    errback_handler()
        Will be called if any exception is raised while processing a
        request generated.
    """

    name = "websites_metrics"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.logger.debug("%s.__init__()", self.__class__.__name__)
        self._urls_provider = UrlsProviderFactory.get_urls_provider(
            settings.CUSTOM_SETTINGS.URLS_PROVIDER_TYPE,
            settings.CUSTOM_SETTINGS.URLS_SRC,
        )

    def start_requests(self):
        """Returns an iterable with the Requests to crawl for this spider.

        It is called by Scrapy when the spider is opened for scraping.
        Scrapy calls it only once, so it is safe to implement
        start_requests() as a generator.
        """

        self.logger.debug("%s.start_requests()", self.__class__.__name__)
        with self._urls_provider as urls_provider:
            for url_data in urls_provider:
                self.logger.debug(
                    "Acquired url_data from provider: %s. Yielding "
                    "scrapy.Request....",
                    url_data,
                )
                yield scrapy.Request(
                    str(url_data.url),
                    callback=self.parse,
                    errback=self.errback_handler,
                    cb_kwargs=dict(regexp=url_data.regexp),
                )

    def parse(self, response: scrapy.http.Response, **kwargs):
        """Callback used by Scrapy to process downloaded responses, when
        their requests don't specify a callback.

        Will collect metrics related to a website link checked:
        - url
        - error_code(status code)
        - response_time
        - regex_pattern
        - matched_text
        """

        regex_pattern = kwargs.get("regexp", "")
        content_type = response.headers.get("Content-Type")
        content_type_is_text_html = b"text/html" in content_type
        download_latency = response.meta.get(
            "download_latency", constants.DEFAULT_RESPONSE_TIME
        )

        self.logger.debug(
            "%s.parse(response=%s, regexp=%s)",
            self.__class__.__name__,
            response,
            regex_pattern,
        )
        self.logger.info("Content-Type: %s", content_type)
        self.logger.info("Content-Type is text/html: %s", content_type_is_text_html)
        self.logger.info("Download latency: %s", download_latency)

        matched_text = ""
        if regex_pattern and content_type_is_text_html:
            re_match = re.search(rf"{regex_pattern}", response.text, re.IGNORECASE)
            if re_match:
                matched_text = re_match.group(0)

        yield MonitorItem(
            url=response.url,
            error_code=str(response.status),
            response_time=download_latency,
            regex_pattern=regex_pattern,
            matched_text=matched_text,
        )

    def errback_handler(self, failure):
        """Will be called if any exception is raised while processing a
        request generated.

        Will collect metrics related to a website link checked:
        - url
        - error_code(status code)
        - response_time
        - regex_pattern
        - matched_text

        failure : twisted.python.failure.Failure
            A basic abstraction for an error that has occurred.
        """

        self.logger.debug(
            "%s.errback_handler(failure=%s)", self.__class__.__name__, repr(failure)
        )

        url = ""
        regex_pattern = ""
        error_code = constants.DEFAULT_STATUS_CODE
        response_time = constants.DEFAULT_RESPONSE_TIME
        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            url = response.url
            regex_pattern = response.request.cb_kwargs.get("regexp")
            response_time = response.meta.get(
                "download_latency", constants.DEFAULT_RESPONSE_TIME
            )
            error_code = response.status
            self.logger.error("HttpError on %s", response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            url = request.url
            regex_pattern = request.cb_kwargs.get("regexp")
            response_time = settings.DNS_TIMEOUT
            # Use 404 for DNS lookup errors:
            error_code = constants.DNS_LOOKUP_ERROR_CODE
            self.logger.error("DNSLookupError on %s", request.url)

        elif failure.check(TwistedTimeoutError, TCPTimedOutError):
            request = failure.request
            url = request.url
            regex_pattern = request.cb_kwargs.get("regexp")
            response_time = settings.DOWNLOAD_TIMEOUT
            error_code = constants.NETWORK_CNX_TIMEOUT_ERROR_CODE
            self.logger.error("TimeoutError on %s", request.url)

        yield MonitorItem(
            url=url,
            error_code=error_code,
            response_time=response_time,
            regex_pattern=regex_pattern,
            matched_text="",
        )


def main():
    """Runs the WebsitesMetricsSpider"""

    # pylint: disable=import-outside-toplevel
    from scrapy.crawler import CrawlerProcess

    process = CrawlerProcess(get_project_settings())
    process.crawl(WebsitesMetricsSpider)
    process.start()


if __name__ == "__main__":
    main()
