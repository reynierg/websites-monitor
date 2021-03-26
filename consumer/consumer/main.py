from concurrent.futures import ThreadPoolExecutor
import inspect
import logging
import logging.config
import os
from queue import Empty, Queue
import types
import typing

from dotenv import load_dotenv
from psycopg2.pool import ThreadedConnectionPool

from common.bounded_executor import BoundedExecutor
from common.db import BoundedThreadedConnectionPool
from common.db import DbManager
from common.delayed_keyboard_interrupt import DelayedKeyboardInterrupt
from common.stream_consumer import StreamConsumerFactory
from consumer.consumer import constants
from consumer.consumer.stream_consumer_thread import StreamConsumerThread


class InitializeStreamConsumerException(Exception):
    """Exception to be thrown when the `StreamConsumer` type specified to be
    instantiated, is not recognized"""


class MainLoop:
    """Implements functionality for bootstrap, teardown, and the main loop of the
    application"""

    def __init__(self):
        """Loads env variables from .env and initialize the logger"""

        load_dotenv(verbose=True, override=True)
        self._consumer_base_dir: str = os.path.dirname(
            os.path.dirname(os.path.abspath(inspect.getfile(
                typing.cast(
                    types.FrameType,
                    inspect.currentframe()
                )
            )))
        )
        self._logger: logging.Logger = self._initialize_logger()
        self._logger.debug("%s.__init__()", self.__class__.__name__)
        self._messages_queue: typing.Optional[Queue] = None
        self._consumer_thread: typing.Optional[StreamConsumerThread] = None

        self._drop_messages_if_abort: bool = \
            not os.getenv("DROP_MESSAGES_IF_ABORT", "0") == "0"
        self._logger.info("drop_messages_if_abort: %s", self._drop_messages_if_abort)
        self._threaded_connection_pool: typing.Optional[ThreadedConnectionPool] = None
        self._db_conn_pool: typing.Optional[BoundedThreadedConnectionPool] = None
        self._db_client: typing.Optional[DbManager] = None
        self._thread_pool_executor: typing.Optional[ThreadPoolExecutor] = None
        self._bounded_executor: typing.Optional[BoundedExecutor] = None

    def _initialize_logger(self) -> logging.Logger:
        """Initialize the logger to be used in the application."""

        log_level: str = os.getenv("LOG_LEVEL", constants.DEFAULT_LOG_LEVEL)
        log_file_handler = constants.LOGGING["handlers"]["loghandler"]
        log_file_handler["level"] = log_level
        log_file_handler["filename"] = \
            f"{self._consumer_base_dir}{os.sep}data{os.sep}logs.log"
        constants.LOGGING["root"]["level"] = log_level

        # print("constants.LOGGING:")
        # pprint.pprint(constants.LOGGING)
        logging.config.dictConfig(constants.LOGGING)
        logger = logging.getLogger("root")
        logger.debug(
            "%s.initialize_logger(filename=%s)",
            self.__class__.__name__, log_file_handler["filename"]
        )
        return logger

    def _init_consumer_thread(
            self,
            stream_consumer_factory: typing.Type[StreamConsumerFactory]
    ):
        """Fires the execution of a KafkaConsumer in a dedicated tread.

        Parameters
        ----------
        stream_consumer_factory : typing.Type[StreamConsumerFactory]
            The factory to be used to instantiate a StreamConsumer
        """

        self._logger.debug("%s._init_consumer_thread()", self.__class__.__name__)
        consumer_type = os.getenv(
            "STREAM_CONSUMER_TYPE",
            constants.DEFAULT_STREAM_CONSUMER_TYPE
        )
        try:
            self._messages_queue = Queue()
            self._consumer_thread = StreamConsumerThread(
                self._messages_queue,
                constants.POLL_TIMEOUT_MS,
                self._drop_messages_if_abort,
                constants.CONSUMER_THREAD_NAME,
                stream_consumer_factory,
                consumer_type,
                constants.LOGGER_NAME,
            )
            self._consumer_thread.start()
            self._logger.info(
                "The '%s' thread was successfully initialized",
                constants.CONSUMER_THREAD_NAME
            )
        except Exception:
            msg = (
                f"Error trying to initialize the '{constants.CONSUMER_THREAD_NAME}' "
                f"thread with stream_consumer_type='{consumer_type}':"
            )
            self._logger.exception(msg)
            raise InitializeStreamConsumerException(msg[:-1]) from None

    def _initialize_db(self):
        self._logger.debug("%s._initialize_db()", self.__class__.__name__)
        self._threaded_connection_pool = ThreadedConnectionPool(
            constants.DB_POOL_MIN_CONN,
            constants.DB_POOL_MAX_CONN,
            dsn=os.getenv("PG_URI"),
        )

        self._db_conn_pool = BoundedThreadedConnectionPool(
            self._threaded_connection_pool,
            constants.DB_POOL_BLOCK_TIMEOUT
        )
        self._logger.info(
            "The BoundedThreadedConnectionPool was successfully initialized"
        )

        current_dir = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))
        )
        sql_file_path = f"{current_dir}{os.sep}{constants.DB_SQL_SCHEMA_FILE_NAME}"
        self._logger.info(
            "Database schema file is expected to be in '%s'",
            sql_file_path
        )
        self._db_client = DbManager(sql_file_path, self._db_conn_pool)
        self._db_client.initialize_db()
        self._logger.info(
            "Database was successfully initialized with schema file in '%s'",
            sql_file_path,
        )

    def _initialize_bounded_thread_pool_executor(self):
        self._logger.debug(
            "%s._initialize_bounded_thread_pool_executor()",
            self.__class__.__name__
        )
        self._thread_pool_executor = ThreadPoolExecutor(
            max_workers=constants.THREAD_POOL_MAX_WORKERS
        )

        self._bounded_executor = BoundedExecutor(
            self._thread_pool_executor,
            constants.THREAD_POOL_QUEUE_MAX_SIZE,
            constants.THREAD_POOL_MAX_WORKERS,
            constants.THREAD_POOL_BLOCK_TIMEOUT,
        )
        self._logger.info(
            "The bounded thread pool executor was successfully initialized"
        )

    def _stop_consumer_thread(self):
        """Stops the consumer thread, and waits for it to finish its execution"""

        self._logger.debug("%s._stop_consumer_thread()", self.__class__.__name__)
        if self._consumer_thread is not None:
            self._logger.info(
                "Signaling the '%s' thread to abort...",
                constants.CONSUMER_THREAD_NAME
            )
            self._consumer_thread.stop()
            self._logger.info(
                "Waiting for the '%s' thread to finish...",
                constants.CONSUMER_THREAD_NAME
            )
            self._consumer_thread.join()
            # At this point all the messages acquired by the consumer_thread
            # should be already stored in the message_queue.
            self._logger.info(
                "The '%s' thread has finished",
                constants.CONSUMER_THREAD_NAME
            )

    def _process_remaining_messages_in_queue(self):
        """Processes the pending work in the messages queue.

        When the signal to abort execution was received, there may have been messages
        left in the message_queue, pending to be stored in the database. Let's process
        them, if any.
        """

        self._logger.debug(
            "%s._process_remaining_messages_in_queue()",
            self.__class__.__name__
        )
        if self._bounded_executor is not None and self._messages_queue is not None:
            if self._drop_messages_if_abort:
                # Notify the threads that are in the thread pool executor blocked
                # waiting for a database connection to abort:
                if self._db_conn_pool is not None:
                    self._logger.info(
                        "Notifying ThreadPool threads waiting for a db connection to "
                        "abort. Already acquired websites metrics that are still in "
                        "the queue will not be processed."
                    )
                    self._db_conn_pool.abort()
            else:
                self._logger.info(
                    "Processing the remaining received messages, which are still in "
                    "the messages_queue..."
                )
                try:
                    while True:
                        msg = self._messages_queue.get(block=False)
                        self._bounded_executor.submit(self._thread_func, msg)
                except Empty:
                    self._logger.info("The messages_queue is empty")

                self._logger.info(
                    "All remaining messages in the messages_queue were sent to the "
                    "thread pool.\nWaiting for pending work in the thread pool to be "
                    "processed..."
                )

            # Wait until all the messages already being processed by the
            # ThreadPool's threads, are persisted in the Postgres database:
            self._bounded_executor.shutdown(wait=True)
            self._logger.info("The pending work in the thread pool was processed")

    def _bootstrap(self):
        """Allocates all the resources required for the messages processing.

        Does the following actions:
        - Fires the execution of a dedicated thread, to get messages from the
          Kafka server.
        - Initializes a database connections pool.
        - Initialize the database(Creates tables 'websites' and 'metrics' if
          they don't exist)
        - Initializes a threads connection pool. It will handles the storage
          of the websites metrics in the Postgres database.
        """

        self._logger.debug("%s._bootstrap()", self.__class__.__name__)
        # If Control+C, SIGTERM or SIGINT take place, they will be delayed until
        # bootstrapping finishes:
        with DelayedKeyboardInterrupt():
            self._init_consumer_thread(StreamConsumerFactory)
            self._initialize_db()
            self._initialize_bounded_thread_pool_executor()

    def _tear_down(self):
        """Implements gracefully shutdown.

        Does the following actions before finish execution:
        - Asks the StreamConsumerThread to abort, and waits for it to finish its
          execution.
        - Processes the pending work in the messages queue, by forwarding them to
          the threads pool, if self._drop_messages_if_abort == False.
        - Waits for the pending work in the threads pool to be processed(Stored
          in the database).
        - Asks the database connections pool, to close all connections.
        """

        try:
            # Shield resources de-allocation for graceful shutdown.
            # If SIGINT/SIGTERM is received during de-allocation, the raise of the
            # KeyboardInterrupt exception will be postponed until all resources are
            # released:
            with DelayedKeyboardInterrupt():
                self._logger.debug("%s._tear_down()", self.__class__.__name__)
                self._stop_consumer_thread()
                self._process_remaining_messages_in_queue()
                if self._db_conn_pool is not None:
                    self._logger.info(
                        "Asking the db connection pool to close all connections..."
                    )
                    self._db_conn_pool.closeall()
                    self._logger.info(
                        "The db connection poll has closed all connections"
                    )
        except KeyboardInterrupt:
            self._logger.warning("KeyboardInterrupt was received during teardown")
        except Exception:  # pylint: disable=broad-except
            self._logger.exception("Error:")

    def _thread_func(
            self,
            website_metrics: typing.Dict[str, typing.Union[str, int, float]]
    ):
        """Stores a website's metrics in the Postgres database.

        This method will be called in a thread pool's thread.

        Parameters
        ----------
        website_metrics : typing.Dict[str, typing.Union[str, int, float]]
            Website metrics to be stored i the database.
        """

        self._logger.debug(
            "%s._thread_func(website_metrics=%s)",
            self.__class__.__name__, website_metrics
        )
        try:
            db_client = typing.cast(DbManager, self._db_client)
            db_client.store_metrics(
                website_metrics["url"],
                website_metrics["regex_pattern"],
                website_metrics["error_code"],
                website_metrics["response_time"],
                website_metrics["matched_text"],
            )
        except Exception:  # pylint: disable=broad-except
            self._logger.exception("Error trying to store website metrics:")

    def run_loop(self):
        """Runs the app main loop"""

        self._logger.debug("%s.run_loop()", self.__class__.__name__)
        try:
            self._bootstrap()
            while True:
                # The main execution thread will block until either, a message is
                # available in the messages_queue, or a SIGINT/SIGTERM/SIGKILL SIGNAL
                # is received. Messages with a website's metrics are stored in the
                # messages_queue by the StreamConsumerThread:
                msg = self._messages_queue.get(block=True)
                self._bounded_executor.submit(self._thread_func, msg)

        except InitializeStreamConsumerException:
            self._logger.exception("Error:")
        except KeyboardInterrupt:
            self._logger.warning("KeyboardInterrupt")
            self._tear_down()
        except Exception:  # pylint: disable=broad-except
            self._logger.exception("Unknown Error: ")
            self._tear_down()


def main():
    """Program's entry point"""

    main_loop = MainLoop()
    main_loop.run_loop()


if __name__ == "__main__":
    main()
