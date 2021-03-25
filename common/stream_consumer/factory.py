"""Contains logic to create a StreamConsumer

This file can be imported as a module and contains the following classes:
    * InvalidStreamConsumerException - Will be throw when the
        `StreamConsumer` type specified to be instantiated, is not recognized
    * StreamConsumerFactory - Provides an instance of the required
        `StreamConsumer`
"""


import importlib
import logging
import os
import typing

from common.kafka_common_config import KAFKA_COMMON_CONFIG
from common.stream_consumer.stream_consumer import StreamConsumer

KAFKA_PROVIDER_NAME = "KafkaStreamConsumer"
DUMMY_PROVIDER_NAME = "DummyStreamConsumer"
IMPORT_INDEX = {
    KAFKA_PROVIDER_NAME: lambda: importlib.import_module(
        "common.stream_consumer.kafka_stream_consumer"
    ),
    DUMMY_PROVIDER_NAME: lambda: importlib.import_module(
        "common.stream_consumer.dummy_stream_consumer"
    ),
}

CONFIG: typing.Dict[
    "str",
    typing.Dict["str", typing.Callable[[], typing.Union[str, None, typing.List[str]]]]
] = {
    "KafkaStreamConsumer": {
        # Delay environment variable evaluation. Wait for that the .env
        # file's content has been loaded into the process's environment, when
        # the corresponding logic load it in main.py:

        "client_id": lambda: os.getenv("CLIENT_ID", "MetricsConsumer1"),
        "consumer_group": lambda: os.getenv("CONSUMER_GROUP", "MetricsCG"),
        "auto_offset_reset": lambda: os.getenv("AUTO_OFFSET_RESET", "earliest"),
        **KAFKA_COMMON_CONFIG
    }
}


class InvalidStreamConsumerException(Exception):
    """Exception to be thrown when the `StreamConsumer` type specified to be
    instantiated, is not recognized"""


class StreamConsumerFactory:
    """Provides an instance of the required StreamConsumer

    Methods
    -------
    get_stream_consumer(stream_consumer_type, *args, **kwargs)
        Returns an instance of the StreamConsumer required
    """

    @staticmethod
    def get_stream_consumer(
        stream_consumer_type: str, *args, **kwargs
    ) -> StreamConsumer:
        """Returns an instance of the StreamConsumer required.

        Parameters
        ----------
        stream_consumer_type : str
            Type of the consumer stream to instantiate.
        args : typing.Tuple
            Additional arguments to be passed to the StreamConsumer
        kwargs : dict
            Additional key-word arguments to be passed to the StreamConsumer

        Returns
        -------
        StreamConsumer
            Concrete instance of the required StreamConsumer.

        Raises
        ------
        InvalidStreamConsumerException
            If the specified stream_consumer_type is not recognized.
        """

        logger = logging.getLogger(kwargs.get("logger_name", __name__))
        logger.debug(
            "StreamConsumerFactory.get_stream_consumer(stream_consumer_type=%s)",
            stream_consumer_type,
        )
        import_statement = IMPORT_INDEX.get(stream_consumer_type)
        if import_statement is None:
            raise InvalidStreamConsumerException(
                f"Specified stream_consumer_type is invalid: {stream_consumer_type}"
            )

        # Evaluate environment variables values if required:
        params = {
            k: v() if callable(v) else v
            for k, v in CONFIG.get(stream_consumer_type, dict()).items()
        }

        if len(kwargs):
            params.update(kwargs)

        logger.debug("params: %s", params)
        stream_consumer_class = getattr(import_statement(), stream_consumer_type)

        return stream_consumer_class(*args, **params)
