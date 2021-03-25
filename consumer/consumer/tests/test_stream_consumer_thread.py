import queue
import random
import time
import typing
import unittest
from unittest import mock

from faker import Faker
from faker.providers import BaseProvider

from common.stream_consumer import DummyStreamConsumer
from common.stream_consumer import StreamConsumerFactory
from consumer.consumer.stream_consumer_thread import StreamConsumerThread
# from .metrics_provider import metrics_provider_fake
# from .metrics_provider import MetricsProvider


class MetricsProvider(BaseProvider):
    urls: typing.List[str] = [
        "https://realpython.com/",
        "https://duckduckgo.com/",
        "https://www.freecodecamp.org/",
        "https://programmingwithmosh.com/"
    ]

    error_codes: typing.List[int] = [200, 201, 301, 404, 500]
    response_times: typing.List[int] = [400, 85, 678, 83, 55]
    regex_patterns: typing.List[str] = \
        [r"\(OK\)", "UP", "UPDATED", "WORKING", r"\d{8}"]
    matched_texts: typing.List[str] = ["(OK)", "UP", "UPDATED", "WORKING", "12345678"]

    class Metrics:
        def __init__(self, url: str, error_code: int, response_time: int,
                     regex_pattern: str, matched_text: str):
            self._url = url
            self._error_code = error_code
            self._response_time = response_time
            self._regex_pattern = regex_pattern
            self._matched_text = matched_text

        @property
        def value(self) -> typing.Dict[str, typing.Union[str, int]]:
            return {
                "url": self._url,
                "error_code": self._error_code,
                "response_time": self._response_time,
                "regex_pattern": self._regex_pattern,
                "matched_text": self._matched_text
            }

    def metrics(self) -> "Metrics":
        random_idx = random.randint(0, len(self.urls) - 1)
        return self.Metrics(
            self.urls[random_idx],
            self.error_codes[random_idx],
            self.response_times[random_idx],
            self.regex_patterns[random_idx],
            self.matched_texts[random_idx]
        )


metrics_provider_fake = Faker()
metrics_provider_fake.add_provider(MetricsProvider)


class TestStreamConsumerThread(unittest.TestCase):
    def setUp(self) -> None:
        self.metrics: typing.List[typing.List[MetricsProvider.Metrics]] = []
        self.connect_was_called = False
        self.disconnect_was_called = False
        self.queue: queue.Queue = queue.Queue()
        self.poll_timeout_ms = 1000
        self.drop_messages_if_abort = False
        self.thread_name = "StreamConsumerThread"

    def _start_thread(self):
        self.stream_consumer_thread: StreamConsumerThread = StreamConsumerThread(
            self.queue,
            self.poll_timeout_ms,
            self.drop_messages_if_abort,
            self.thread_name,
            StreamConsumerFactory,
            "whatever"
        )
        self.stream_consumer_thread.start()

    def poll(self, timeout_ms=0, max_records=None, **kwargs):
        """Generates random websites metrics data for the StreamConsumerThread"""

        count = random.randint(1, 6)
        self.metrics.append([metrics_provider_fake.metrics() for _ in range(count)])
        return {"partition1": self.metrics[-1]}

    def connect(self):
        """WIll be called by the """
        self.connect_was_called = True

    def disconnect(self):
        self.disconnect_was_called = True

    @mock.patch.object(StreamConsumerFactory, "get_stream_consumer")
    def test_thread_poll_messages_and_put_them_in_the_queue(
            self, mock_get_stream_consumer
    ):
        # The DummyStreamConsumer will forward any call from the StreamConsumerThread
        # to this test class's instance:
        dummy_consumer = DummyStreamConsumer(mock_obj=self)
        mock_get_stream_consumer.return_value = dummy_consumer
        self._start_thread()
        time.sleep(1)
        # When the StreamConsumerThread starts execution, it will use a factory
        # to get a StreamConsumer object, because of the patch, it will get a
        # DummyStreamConsumer with this test class's instance as a test double. The
        # DummyStreamConsumer will forward every call from the DummyStreamConsumer to
        # this object:
        self.assertTrue(self.connect_was_called)
        self.stream_consumer_thread.stop()
        self.stream_consumer_thread.join()
        self.assertTrue(self.disconnect_was_called)

        generated_metrics = \
            [metrics.value for metrics_list in self.metrics for metrics in metrics_list]
        generated_metrics.sort(key=lambda item: item['url'])
        print(f"generated_metrics: {generated_metrics}")
        queue_items = []
        try:
            while True:
                queue_items.append(self.queue.get(block=False))
        except queue.Empty:
            pass

        queue_items.sort(key=lambda item: item['url'])

        print(f"queue_items: {queue_items}")

        self.assertListEqual(generated_metrics, queue_items)
