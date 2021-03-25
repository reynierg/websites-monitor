# pylint: disable=missing-function-docstring

import os
from unittest import mock

from common.stream_consumer import StreamConsumerFactory
from common.stream_consumer.kafka_stream_consumer import KafkaStreamConsumer


ENV_VARS = {
    "BOOTSTRAP_SERVERS": "localhost",
    "SECURITY_PROTOCOL": "SSL",
    "SSL_CAFILE": "ca.pem",
    "SSL_CERTFILE": "service.cert",
    "SSL_KEYFILE": "service.key",
    "TOPIC_NAME": "test_topic",
    "CLIENT_ID": "client_id",
    "CONSUMER_GROUP": "consumer_group",
    "AUTO_OFFSET_RESET": "earliest",
}


@mock.patch.dict(os.environ, ENV_VARS)
@mock.patch(
    "common.stream_consumer.kafka_stream_consumer.KafkaConsumer",
    autospec=True
)
def test_context_manager(mock_kafka_consumer):
    stream_consumer: KafkaStreamConsumer
    with StreamConsumerFactory.get_stream_consumer("KafkaStreamConsumer") \
            as stream_consumer:
        assert isinstance(stream_consumer, KafkaStreamConsumer)
        mock_kafka_consumer.assert_called_once_with(
            "test_topic",
            auto_offset_reset="earliest",
            bootstrap_servers=["localhost"],
            client_id="client_id",
            group_id="consumer_group",
            security_protocol="SSL",
            ssl_cafile="ca.pem",
            ssl_certfile="service.cert",
            ssl_keyfile="service.key",
            value_deserializer=stream_consumer.message_deserializer,
        )

    mock_kafka_consumer.return_value.close.assert_called_once()


@mock.patch.dict(os.environ, {"BOOTSTRAP_SERVERS": "localhost"})
@mock.patch(
    "common.stream_consumer.kafka_stream_consumer.KafkaConsumer",
    autospec=True
)
def test_underlying_poll(mock_kafka_consumer):
    with StreamConsumerFactory.get_stream_consumer("KafkaStreamConsumer") \
            as stream_consumer:
        stream_consumer.poll()
        mock_kafka_consumer.return_value.poll.assert_called_once_with(0, None)


@mock.patch.dict(
    os.environ,
    ENV_VARS,
)
@mock.patch(
    "common.stream_consumer.kafka_stream_consumer.KafkaConsumer",
    autospec=True
)
def test_connect(mock_kafka_consumer):
    stream_consumer = StreamConsumerFactory.get_stream_consumer("KafkaStreamConsumer")
    assert isinstance(stream_consumer, KafkaStreamConsumer)
    stream_consumer.connect()
    mock_kafka_consumer.assert_called_once_with(
        "test_topic",
        auto_offset_reset="earliest",
        bootstrap_servers=["localhost"],
        client_id="client_id",
        group_id="consumer_group",
        security_protocol="SSL",
        ssl_cafile="ca.pem",
        ssl_certfile="service.cert",
        ssl_keyfile="service.key",
        value_deserializer=stream_consumer.message_deserializer,
    )


@mock.patch.dict(os.environ, {"BOOTSTRAP_SERVERS": "localhost"})
@mock.patch(
    "common.stream_consumer.kafka_stream_consumer.KafkaConsumer",
    autospec=True
)
def test_disconnect(mock_kafka_consumer):
    stream_consumer = StreamConsumerFactory.get_stream_consumer("KafkaStreamConsumer")
    stream_consumer.connect()
    stream_consumer.disconnect()
    mock_kafka_consumer.return_value.close.assert_called_once()
