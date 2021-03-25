"""Contains logic to create a StreamProducer

This file can be imported as a module and contains the following classes:
    * InvalidStreamProducerException - Will be throw when the
        `StreamProducer` type specified to be instantiated, is not recognized
    * StreamProducerFactory - Provides an instance of the required
        `StreamProducer`
"""

import importlib
import logging
import typing

from common.kafka_common_config import KAFKA_COMMON_CONFIG
from .stream_producer import StreamProducer

KAFKA_PROVIDER_NAME = "KafkaStreamProducer"
IMPORT_INDEX = {
    KAFKA_PROVIDER_NAME: lambda: importlib.import_module(
        "common.stream_producer.kafka_stream_producer"
    )
}

CONFIG: typing.Dict[str, dict] = {
    KAFKA_PROVIDER_NAME: KAFKA_COMMON_CONFIG
}


class InvalidStreamProducerException(Exception):
    """Exception to be thrown when the `StreamProducer` type specified to be
    instantiated, is not recognized"""


class StreamProducerFactory:
    """Provides an instance of the required StreamProducer

    Methods
    -------
    get_stream_producer(stream_producer_type, *args, **kwargs)
        Returns an instance of the StreamProducer required
    """

    @staticmethod
    def get_stream_producer(
        stream_producer_type: str, *args, **kwargs
    ) -> StreamProducer:
        """Returns an instance of the StreamProducer required.

        Parameters
        ----------
        stream_producer_type : str
            Type of the producer stream to instantiate.
        args : typing.Tuple
            Additional arguments to be passed to the StreamProducer
        kwargs : dict
            Additional key-word arguments to be passed to the StreamProducer

        Returns
        -------
        StreamProducer
            Concrete instance of the required StreamProducer.

        Raises
        ------
        InvalidStreamProducerException
            If the specified stream_producer_type is not recognized.
        """

        logger = logging.getLogger(kwargs.get("logger_name", __name__))
        logger.debug(
            "StreamProducerFactory.get_stream_producer(stream_producer_type=%s)",
            stream_producer_type,
        )
        import_statement = IMPORT_INDEX.get(stream_producer_type)
        if not import_statement:
            raise InvalidStreamProducerException(
                f"Specified stream_producer_type is invalid: {stream_producer_type}"
            )

        # Evaluate environment variables values if required:
        params = {
            k: v() if callable(v) else v
            for k, v in CONFIG.get(stream_producer_type, dict()).items()
        }

        if len(kwargs):
            params.update(kwargs)

        logger.debug("params: %s", params)
        stream_producer_class = getattr(import_statement(), stream_producer_type)

        return stream_producer_class(*args, **params)
