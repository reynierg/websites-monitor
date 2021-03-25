# pylint: disable=missing-function-docstring

import os
from unittest import mock

from common.stream_producer import StreamProducerFactory
from common.stream_producer.kafka_stream_producer import KafkaStreamProducer


@mock.patch.dict(
    os.environ,
    {
        "BOOTSTRAP_SERVERS": "localhost",
        "SECURITY_PROTOCOL": "SSL",
        "SSL_CAFILE": "ca.pem",
        "SSL_CERTFILE": "service.cert",
        "SSL_KEYFILE": "service.key",
        "TOPIC_NAME": "test_topic",
    },
)
@mock.patch(
    "common.stream_producer.kafka_stream_producer.KafkaProducer",
    autospec=True
)
def test_connect_underlying_kafka_producer_is_instantiated(mock_kafka_producer):
    stream_producer = StreamProducerFactory.get_stream_producer("KafkaStreamProducer")
    stream_producer.connect()
    assert isinstance(stream_producer, KafkaStreamProducer)
    mock_kafka_producer.assert_called_once_with(
        bootstrap_servers=["localhost"],
        security_protocol="SSL",
        ssl_cafile="ca.pem",
        ssl_certfile="service.cert",
        ssl_keyfile="service.key",
        value_serializer=stream_producer.message_serializer,
    )


@mock.patch.dict(os.environ, {"BOOTSTRAP_SERVERS": "localhost"})
@mock.patch("common.stream_producer.kafka_stream_producer.KafkaProducer", autospec=True)
def test_disconnect_underlying_close_method_is_called(mock_kafka_producer):
    stream_producer = StreamProducerFactory.get_stream_producer("KafkaStreamProducer")
    stream_producer.connect()
    stream_producer.disconnect()
    mock_kafka_producer.return_value.close.assert_called_once()


@mock.patch.dict(
    os.environ, {"BOOTSTRAP_SERVERS": "localhost", "TOPIC_NAME": "test_topic"}
)
@mock.patch("common.stream_producer.kafka_stream_producer.KafkaProducer", autospec=True)
def test_persist_data_underlying_send_and_flush_methods_are_called(mock_kafka_producer):
    stream_producer = StreamProducerFactory.get_stream_producer("KafkaStreamProducer")
    stream_producer.connect()
    dummy_data = {"url": "https://google.com"}
    stream_producer.persist_data(dummy_data)
    mock_kafka_producer.return_value.send.assert_called_once_with(
        "test_topic", value=dummy_data
    )
    mock_kafka_producer.return_value.flush.assert_called_once()
