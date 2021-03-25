"""Provide definition of abstract Stream Consumers

This file can be imported as a module and contains the following classes:
    * StreamConsumer - Abstract class that must be implement by concrete
        Stream Consumers
"""

import abc
import logging
import types
import typing


class StreamConsumer(abc.ABC):
    """Abstract class that must be implement by concrete Stream Consumers"""

    def __init__(self, **kwargs):
        """Initializes the logger to be used

        Parameters
        ----------
        kwargs : dict
             logger_name : str
                Logger's name.
        """

        logger_name = kwargs.get("logger_name", __name__)
        self._logger = logging.getLogger(logger_name)
        self._logger.debug("StreamConsumer.__init__(logger_name=%s)", logger_name)

    def __enter__(self) -> "StreamConsumer":
        self._logger.debug("StreamConsumer.__enter__()")
        self.connect()
        return self

    def __exit__(
            self,
            exc_type: typing.Optional[typing.Type[BaseException]],
            exc_val: typing.Optional[BaseException],
            exc_tb: typing.Optional[types.TracebackType],
    ):
        self._logger.debug("StreamConsumer.__exit__()")
        self.disconnect()

    def __iter__(
        self,
    ) -> typing.Generator[typing.Dict[str, typing.Union[str, int]], None, None]:
        self._logger.debug("StreamConsumer.__iter__(...)")
        return self.generator

    @abc.abstractmethod
    def connect(self):
        """Establish the required connections with the Stream Server."""

    @abc.abstractmethod
    def disconnect(self):
        """Closes the consumer, and waits for connections to be closed."""

    @abc.abstractmethod
    def poll(self, timeout_ms=0, max_records=None, **kwargs):
        """Fetch data from corresponding Stream

        Parameters
        ----------
        timeout_ms : int
            Milliseconds spent waiting in poll if data is not available in
            the stream.
        max_records : int
            The maximum number of records returned in a single call.
        kwargs : dict
            Optional keyword arguments.
        """

    @property
    @abc.abstractmethod
    def generator(
        self,
    ) -> typing.Generator[typing.Dict[str, typing.Union[str, int]], None, None]:
        """Provides an iterator for consume the corresponding stream"""
