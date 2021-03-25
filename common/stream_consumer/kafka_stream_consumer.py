"""Provides functionality to consume websites metrics from a Kafka cluster.

This file can be imported as a module and contains the following classes:
    * KafkaStreamConsumer - Consumes records from a Kafka cluster.
"""

import json
import typing

from kafka import KafkaConsumer

from .stream_consumer import StreamConsumer


class KafkaStreamConsumer(StreamConsumer):
    """Consumes records from a Kafka cluster.

    Methods
    -------
    poll(timeout_ms=0, max_records=None, *args, **kwargs)
        Fetch data from assigned topics / partitions.
    close()
        Closes the consumer, waiting indefinitely for any needed cleanup.
    generator()
        Provides an iterator for consume the Kafka stream.
    """

    def __init__(
        self, bootstrap_servers: typing.List[str], security_protocol: str,
        ssl_cafile: str, ssl_certfile: str, ssl_keyfile: str, topic_name: str,
        client_id: str, consumer_group: str, auto_offset_reset: str, **kwargs
    ):
        """

        Parameters
        ----------
        bootstrap_servers : typing.List[str]
            list of 'host[:port]'strings that the consumer should contact to
            bootstrap initial cluster metadata. This does not have to be the
            full node list. It just needs to have at least one broker that
            will respond to a Metadata API Request. Default port is 9092. If
            no servers are specified, will default to localhost:9092.
        security_protocol : str
            Protocol used to communicate with brokers. Valid values are:
            PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL.
        ssl_cafile : str
            Optional filename of ca file to use in certificate verification.
        ssl_certfile : str
            Optional filename of file in pem format containing the client
            certificate, as well as any ca certificates needed to establish
            the certificate's authenticity.
        ssl_keyfile : str
            Optional filename containing the client private key.
        topic_name : str
            Topic to subscribe to.
        client_id : str
            A name for this client. This string is passed in each request to
            servers and can be used to identify specific server-side log
            entries that correspond to this client. Also submitted to
            GroupCoordinator for logging with respect to consumer group
            administration.
        consumer_group : str
            The name of the consumer group to join for dynamic partition
            assignment (if enabled), and to use for fetching and committing
            offsets. If None, auto-partition assignment (via group
            coordinator) and offset commits are disabled.
        auto_offset_reset : str
            A policy for resetting offsets on OffsetOutOfRange errors:
            'earliest' will move to the oldest available message, 'latest'
            will move to the most recent. Any other value will raise the
            exception. Default: 'latest'.
        kwargs : dict
            logger_name : str, optional
            The name of the logger.
        """

        super().__init__(**kwargs)
        self._logger.debug(
            "%s.__init__(bootstrap_servers=%s, security_protocol=%s, ssl_cafile=%s, "
            "ssl_certfile=%s, ssl_keyfile=%s, topic_name=%s, client_id=%s, "
            "consumer_group=%s, auto_offset_reset=%s)", self.__class__.__name__,
            bootstrap_servers, security_protocol, ssl_cafile, ssl_certfile,
            ssl_keyfile, topic_name, client_id, consumer_group, auto_offset_reset
        )
        self._bootstrap_servers = bootstrap_servers
        self._security_protocol = security_protocol
        self._ssl_cafile = ssl_cafile
        self._ssl_certfile = ssl_certfile
        self._ssl_keyfile = ssl_keyfile
        self._topic_name = topic_name
        self._client_id = client_id
        self._consumer_group = consumer_group
        self._auto_offset_reset = auto_offset_reset
        self._kafka_consumer: typing.Optional[KafkaConsumer] = None

    def connect(self):
        """Initializes a KafkaConsumer"""

        self._logger.debug("%s.connect()", self.__class__.__name__)
        self._kafka_consumer = KafkaConsumer(
            self._topic_name,
            bootstrap_servers=self._bootstrap_servers,
            client_id=self._client_id,
            group_id=self._consumer_group,
            security_protocol=self._security_protocol,
            ssl_cafile=self._ssl_cafile,
            ssl_certfile=self._ssl_certfile,
            ssl_keyfile=self._ssl_keyfile,
            auto_offset_reset=self._auto_offset_reset,
            value_deserializer=self.message_deserializer,
        )

    def disconnect(self):
        """Closes the consumer, and waits for connections to be closed.

        The consumer will attempt to commit any pending consumed offsets
        prior to close.
        """

        self._logger.debug("%s.close()", self.__class__.__name__)
        if self._kafka_consumer is not None:
            self._kafka_consumer.close()
            self._logger.info("Connection with Kafka was successfully closed")

    @staticmethod
    def message_deserializer(msg):
        """Called to deserialize a message acquired from the Kafka server"""

        return json.loads(msg.decode("ascii"))

    def _consume_messages(self):
        self._logger.debug("%s._consume_messages()", self.__class__.__name__)
        for msg in self._kafka_consumer:
            yield msg

    def poll(self, timeout_ms=0, max_records=None, **kwargs):
        """Fetch data from assigned topics / partitions.

        Records are fetched and returned in batches by topic-partition.
        On each poll, consumer will try to use the last consumed offset as the
        starting offset and fetch sequentially. The last consumed offset can be
        manually set through :meth:`~kafka.KafkaConsumer.seek` or automatically
        set as the last committed offset for the subscribed list of partitions.

        Incompatible with iterator interface -- use one or the other, not both.

        Parameters
        ----------
        timeout_ms : int
            Milliseconds spent waiting in poll if data is not available in
            the buffer. If 0, returns immediately with any records that are
            available currently in the buffer, else returns empty. Must not
            be negative (default is 0).
        max_records : int
            The maximum number of records returned in a single call to
            :meth:`~kafka.KafkaConsumer.poll` (default is inherit value from
            max_poll_records).

        Returns
        -------
        dict
            Topic to list of records since the last fetch for the subscribed
            list of topics and partitions.
        """

        self._logger.debug(
            "%s.poll(timeout_ms=%s, max_records=%s)",
            self.__class__.__name__,
            timeout_ms,
            max_records,
        )
        return self._kafka_consumer.poll(timeout_ms, max_records, **kwargs)

    @property
    def generator(
        self,
    ) -> typing.Generator[typing.Dict[str, typing.Union[str, int]], None, None]:
        """Provides an iterator for consume the Kafka stream."""

        self._logger.debug("%s.generator()", self.__class__.__name__)
        if self._kafka_consumer is None:
            raise Exception("Kafka consumer is already closed!!!")

        return self._consume_messages()
