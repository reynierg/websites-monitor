"""Defines the item pipelines to be used

Don't forget to add your pipeline to the ITEM_PIPELINES setting
See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

This file can be imported as a module and contains the following classes:
    * MonitorPipeline - Store a website's metrics in a Kafka topic.
"""

import logging
import typing

# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter

from common.stream_producer import StreamProducer
from common.stream_producer import StreamProducerFactory

from . import settings


class MonitorPipeline:
    """After an item has been scraped by a spider, it is sent to the Item
    Pipeline which processes it through several components that are executed
    sequentially.

    Each item pipeline component (sometimes referred as just “Item Pipeline”)
    is a Python class that implements a simple method. They receive an item
    and perform an action over it, also deciding if the item should continue
    through the pipeline or be dropped and no longer processed.

    This pipeline will store a website's metrics in a Kafka topic.

    Methods
    -------
    open_spider(spider)
        Will be called when the spider is opened
    close_spider(spider)
        Will be called when the spider is closed
    process_item(item, spider)
        Processes a website metrics item created by the Spider
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._logger.debug("%s.__init__()", self.__class__.__name__)
        self._streaming_provider: typing.Optional[StreamProducer] = None

    def open_spider(self, spider):
        """Will be called when the spider is opened.

        Creates a KafkaProducer.
        """

        # pylint: disable=unused-argument
        self._streaming_provider = StreamProducerFactory.get_stream_producer(
            settings.CUSTOM_SETTINGS.STREAM_PRODUCER_TYPE
        )
        self._streaming_provider.connect()

    def close_spider(self, spider):
        """Will be called when the spider is closed."""

        # pylint: disable=unused-argument
        self._streaming_provider.disconnect()

    def process_item(self, item, spider):
        """Processes a website metrics item created by the Spider.

        It will save the website metrics in the Kafka Server.
        This method is called for every item pipeline component.
        """

        # pylint: disable=unused-argument
        self._logger.debug("%s.process_item(%s)", self.__class__.__name__, item)
        data = {k: item[k] for k in item.keys()}
        self._streaming_provider.persist_data(data)
        return item
