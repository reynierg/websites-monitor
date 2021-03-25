import os
import typing

KAFKA_COMMON_CONFIG: typing.Dict[
    str,
    typing.Callable[[], typing.Union[str, None, typing.List[str]]]
] = {
    # Delay environment variable evaluation. Wait for that the .env
    # file's content has been loaded into the process's environment, when
    # the corresponding logic load it in main.py:

    # list of ‘host[:port]’ strings that the consumer should
    # contact to bootstrap initial cluster metadata. This does
    # not have to be the full node list. It just needs to have
    # at least one broker that will respond to a Metadata API
    # Request. Default port is 9092. If no servers are
    # specified, will default to localhost:9092.
    "bootstrap_servers": lambda: os.getenv(
        "BOOTSTRAP_SERVERS", "localhost:9092"
    ).split(","),
    # Protocol used to communicate with brokers. Valid values
    # are: PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL. Default:
    # PLAINTEXT.
    "security_protocol": lambda: os.getenv("SECURITY_PROTOCOL", "SSL"),
    # Optional filename of ca file to use in certificate
    # verification. Default: None.
    "ssl_cafile": lambda: os.getenv("SSL_CAFILE", "/app/kafka_certs/ca.pem"),
    # Optional filename of file in pem format containing the
    # client certificate, as well as any ca certificates needed
    # to establish the certificate’s authenticity.
    # Default: None.
    "ssl_certfile": lambda: os.getenv("SSL_CERTFILE", "/app/kafka_certs/service.cert"),
    # Optional filename containing the client private key.
    # Default: None.
    "ssl_keyfile": lambda: os.getenv("SSL_KEYFILE", "/app/kafka_certs/service.key"),
    # Topic to subscribe to.
    "topic_name": lambda: os.getenv("TOPIC_NAME"),
}
