# pylint: disable=missing-function-docstring

import uuid

import pytest

from common.stream_consumer import InvalidStreamConsumerException
from common.stream_consumer import StreamConsumerFactory
from common.stream_consumer.kafka_stream_consumer import KafkaStreamConsumer


def test_kafka_stream_consumer_is_instantiated():
    stream_consumer = StreamConsumerFactory.get_stream_consumer("KafkaStreamConsumer")
    assert isinstance(stream_consumer, KafkaStreamConsumer)


def test_create_invalid_stream_consumer():
    invalid_stream_consumer_name = str(uuid.uuid4())
    except_msg = (
        f"Specified stream_consumer_type is invalid: {invalid_stream_consumer_name}"
    )
    with pytest.raises(InvalidStreamConsumerException, match=except_msg):
        StreamConsumerFactory.get_stream_consumer(
            invalid_stream_consumer_name,
        )
