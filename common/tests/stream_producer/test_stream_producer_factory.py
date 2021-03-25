# pylint: disable=missing-function-docstring

from unittest import mock
import uuid

import pytest

from common.stream_producer import InvalidStreamProducerException
from common.stream_producer import StreamProducerFactory
from common.stream_producer.kafka_stream_producer import KafkaStreamProducer


@mock.patch(
    "common.stream_producer.kafka_stream_producer.KafkaProducer",
    autospec=True
)
def test_kafka_stream_consumer_is_instantiated(mock_kafka_producer):
    # pylint: disable=unused-argument
    stream_producer = StreamProducerFactory.get_stream_producer("KafkaStreamProducer")
    assert isinstance(stream_producer, KafkaStreamProducer)


def test_create_invalid_stream_consumer():
    invalid_stream_producer_name = str(uuid.uuid4())
    except_msg = (
        f"Specified stream_producer_type is invalid: " f"{invalid_stream_producer_name}"
    )
    with pytest.raises(InvalidStreamProducerException, match=except_msg):
        StreamProducerFactory.get_stream_producer(
            invalid_stream_producer_name,
        )
