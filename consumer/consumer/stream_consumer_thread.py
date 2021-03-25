"""Provides functionality for consume websites metrics from a Kafka Cluster.

It will consume the messages from the corresponding topic in a dedicated
execution thread.

This file can be imported as a module and contains the following classes:
    * AbortException - Raised to notify that the thread should immediately abort
        execution
    * StreamConsumerThread - Consumes data from a Kafka cluster in a
        dedicated execution thread
"""

import logging
from queue import Queue
import threading
import typing

from common.stream_consumer import InvalidStreamConsumerException
from common.stream_consumer import StreamConsumer


class AbortException(Exception):
    """Raised to notify that the thread should immediately abort execution"""


class StreamConsumerThread(threading.Thread):
    """Consumes data from a Kafka cluster in a dedicated execution thread

    Implements logic for in a dedicated execution thread, acquire generated
    website metrics, and store them in a queue of metrics to be processed.

    Methods
    -------
    run()
        Executes the thread entry point.
    stop()
        Notifies the thread, that it should abort execution.
    """

    WAIT_TIME_BETWEEN_POLL = 1

    def __init__(
        self,
        queue: Queue,
        poll_timeout_ms: int,
        drop_messages_if_abort: bool,
        thread_name: str,
        stream_consumer_factory,
        stream_consumer_type: str,
        logger_name: typing.Optional[str] = None,
    ):
        """

        Parameters
        ----------
        queue : queue.Queue
            The thread will store the acquired messages in this queue
        poll_timeout_ms : int
            Milliseconds spent waiting in poll if data is not available in
            the buffer. If 0, returns immediately with any records that are
            available currently in the buffer, else returns empty. Must not
            be negative.
        drop_messages_if_abort : bool
            Specifies if the acquired messages as a result of call poll,
            should or not be drop, when abort is required.
            If False, the acquired messages will be stored in the queue,
            before abort execution.
            If True, the acquired messages will be dropped.
        thread_name : str
            Name to be used for the stream consumer thread.
        stream_consumer_factory : class
            Factory to be used to create a stream consumer of the specified
            type.
        stream_consumer_type : str
            Name of the stream consumer to be used.
        logger_name : typing.Optional[str]
            Logger's name
        """

        threading.Thread.__init__(self, name=thread_name, daemon=False)
        self._queue: Queue = queue
        self._poll_timeout_ms: int = poll_timeout_ms
        self._drop_messages_if_abort: bool = drop_messages_if_abort
        self._stream_consumer_factory = stream_consumer_factory
        self._stream_consumer_type: str = stream_consumer_type
        self._logger_name: str = logger_name or __name__
        self._abort_event: threading.Event = threading.Event()

        self._logger = logging.getLogger(self._logger_name)
        self._logger.debug(
            "%s.__init__(poll_timeout_ms=%s, drop_messages_if_abort=%s, "
            "thread_name=%s, stream_consumer_type=%s, logger_name=%s)",
            self.__class__.__name__, poll_timeout_ms, drop_messages_if_abort,
            thread_name, stream_consumer_type, self._logger_name
        )

    def _extract_messages_payload(self, pool_result) \
            -> typing.Generator[dict, None, None]:
        self._logger.debug("%s._extract_messages_payload()", self.__class__.__name__)
        for _, messages in pool_result.items():
            for message in messages:
                if (
                        self._abort_event.is_set()
                        and self._drop_messages_if_abort
                ):
                    raise AbortException(
                        "Abort event was signaled and self._drop_messages_if_abort is "
                        "True. Acquired messages will be dropped"
                    )

                yield message.value

    def run(self) -> None:
        """Executes the thread entry point.

        It will be running until notified for abort execution.
        When notified to abort, if self._drop_messages_if_abort is True, the
        metrics acquired from the Kafka cluster will be discarded.
        """

        self._logger.debug("%s.run()", self.__class__.__name__)
        try:
            stream_consumer: StreamConsumer
            with self._stream_consumer_factory.get_stream_consumer(
                    stream_consumer_type=self._stream_consumer_type,
                    logger_name=self._logger_name
            ) as stream_consumer:
                while True:
                    self._logger.debug(
                        "Trying to get messages from the StreamConsumer..."
                    )
                    results = stream_consumer.poll(self._poll_timeout_ms)
                    for message_payload in self._extract_messages_payload(results):
                        self._queue.put(message_payload)

                    if self._abort_event.wait(self.WAIT_TIME_BETWEEN_POLL):
                        self._logger.info("Abort event was signaled")
                        break
        except InvalidStreamConsumerException:
            self._logger.exception(
                "Error trying to start the execution of the '%s' thread with the '%s' "
                "consumer:", self.name, self._stream_consumer_type
            )
        except AbortException:
            self._logger.exception("Notified to abort execution:")
        except Exception:  # pylint: disable=broad-except
            self._logger.exception("An unknown error happened:")
        finally:
            self._logger.info("Aborting thread: '%s' execution. ", self.name)

    def stop(self):
        """Notifies this instance of the `StreamConsumerThread` thread, that
        it should abort execution.

        Implements graceful shutdown.
        """

        self._logger.debug("%s.stop()", self.__class__.__name__)
        self._logger.info("Asking thread '%s' to abort execution", self.name)
        self._abort_event.set()
