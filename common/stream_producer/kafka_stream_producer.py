"""Provides functionality to publish websites metrics to a Kafka cluster.

This file can be imported as a module and contains the following classes:
    * KafkaStreamProducer - Publish records to a Kafka cluster.
"""

import json
import typing

from kafka import KafkaProducer

from .stream_producer import StreamProducer


class KafkaProducerIsNotConnected(Exception):
    """Raised when trying to interact with the Kafka server without connect first"""


class KafkaStreamProducer(StreamProducer):
    """Publishes records to a Kafka cluster.

    Methods
    -------
    connect(timeout_ms=0, max_records=None, *args, **kwargs)
        Fetch data from assigned topics / partitions.
    close()
        Closes the consumer, waiting indefinitely for any needed cleanup.
    generator()
        Provides an iterator for consume the Kafka stream.
    """

    def __init__(
        self, bootstrap_servers: typing.List[str], security_protocol: str,
        ssl_cafile: str, ssl_certfile: str, ssl_keyfile: str, topic_name: str, **kwargs
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
        kwargs : dict
            logger_name : str, optional
            The name of the logger.
        """

        super().__init__(**kwargs)
        self._logger.debug(
            "%s.__init__(bootstrap_servers=%s, security_protocol=%s, ssl_cafile=%s, "
            "ssl_certfile=%s, ssl_keyfile=%s, topic_name=%s)",
            self.__class__.__name__, bootstrap_servers, security_protocol, ssl_cafile,
            ssl_certfile, ssl_keyfile, topic_name,
        )
        self._bootstrap_servers = bootstrap_servers
        self._security_protocol = security_protocol
        self._ssl_cafile = ssl_cafile
        self._ssl_certfile = ssl_certfile
        self._ssl_keyfile = ssl_keyfile
        self._topic_name = topic_name

        self._kafka_producer: typing.Optional[KafkaProducer] = None

    def connect(self):
        """Instantiates a KafkaProducer.

        Establish the required connections with a Kafka Cluster.
        """

        self._logger.debug("%s.connect()", self.__class__.__name__)
        self._kafka_producer = KafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            security_protocol=self._security_protocol,
            ssl_cafile=self._ssl_cafile,
            ssl_certfile=self._ssl_certfile,
            ssl_keyfile=self._ssl_keyfile,
            value_serializer=self.message_serializer,
        )

    @staticmethod
    def message_serializer(data_dict):
        """Called to serialize a message to be sent to the Kafka server"""

        return json.dumps(data_dict).encode("ascii")

    def disconnect(self):
        """Closes all connections with te Kafka cluster

        Raises
        ------
        KafkaProducerIsNotConnected
            when trying to interact with the Kafka server without connect first
        """

        self._logger.debug("%s.disconnect()", self.__class__.__name__)
        if self._kafka_producer is None:
            raise KafkaProducerIsNotConnected()

        self._kafka_producer.close()
        self._logger.info("Connection with Kafka was successfully closed")

    def persist_data(self, data: typing.Dict[str, typing.Union[str, int]]):
        """Persist a dict with the website metrics in the corresponding topic.

        Parameters
        ----------
        data : typing.Dict[str, typing.Union[str, int]]
            Website metrics

        Raises
        ------
        KafkaProducerIsNotConnected
            when trying to interact with the Kafka server without connect first
        """

        self._logger.debug("%s.persist_data()", self.__class__.__name__)
        if self._kafka_producer is None:
            raise KafkaProducerIsNotConnected()

        self._kafka_producer.send(self._topic_name, value=data)
        self._kafka_producer.flush()
        self._logger.info("Data was persisted successfully to Kafka")
