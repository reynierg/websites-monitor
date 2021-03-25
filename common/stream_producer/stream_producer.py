"""Provide definition of abstract Stream Producer

This file can be imported as a module and contains the following classes:
    * StreamProducer - Abstract class that must be implement by concrete
        Stream Producers
"""

import abc
import logging
import types
import typing


class StreamProducer(abc.ABC):
    """Abstract class that must be implement by concrete Stream Producers"""

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
        self._logger.debug("StreamProducer.__init__(logger_name=%s)", logger_name)

    def __enter__(self):
        self._logger.debug("StreamProducer.__enter__()")
        self.connect()

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ):
        self._logger.debug("StreamProducer.__exit__()")
        self.disconnect()

    @abc.abstractmethod
    def connect(self):
        """Establish the required connections with the Stream Server."""

    @abc.abstractmethod
    def disconnect(self):
        """Closes all connections with the Stream Server"""

    @abc.abstractmethod
    def persist_data(self, data: typing.Dict[str, typing.Union[str, int]]):
        """Persist a dict with the website metrics in the corresponding
        Stream Server.

        data : typing.Dict[str, typing.Union[str, int]]
            Website metrics
        """
