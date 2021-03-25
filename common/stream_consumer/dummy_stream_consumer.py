"""Provides functionality for a dummy stream consumer.

This file can be imported as a module and contains the following classes:
    * DummyStreamConsumer - Consumes records from a Kafka cluster.
"""

import typing

from .stream_consumer import StreamConsumer


class DummyStreamConsumer(StreamConsumer):
    """Provides a dummy stream consumer for tests purpose that will forward every
    call to the mock_obj"""

    def __init__(self, **kwargs):
        """

        Parameters
        ----------
        kwargs:
            logger_name : str
                Logger's name.
            mock_obj : MagicMock
        """

        self._mock_obj = kwargs.get("mock_obj", None)
        super().__init__(**kwargs)

    def poll(self, timeout_ms=0, max_records=None, **kwargs):
        """Dummy poll. Hand over the method call to the mock_obj"""

        return self._mock_obj.poll(timeout_ms=0, max_records=None, **kwargs) \
            if self._mock_obj else dict()

    @property
    def generator(self) \
            -> typing.Generator[
                typing.Dict[str, typing.Union[str, int]],
                None,
                None
            ]:
        """Dummy generator"""

        raise NotImplementedError()

    def connect(self):
        """Dummy connect. Hand over the method call to the mock_obj"""

        if self._mock_obj:
            self._mock_obj.connect()

    def disconnect(self):
        """Dummy disconnect. Hand over the method call to the mock_obj"""

        if self._mock_obj:
            self._mock_obj.disconnect()
