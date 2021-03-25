import logging
import os
import typing

DEFAULT_STREAM_CONSUMER_TYPE = "KafkaStreamConsumer"

DB_POOL_MIN_CONN = 4
DB_POOL_MAX_CONN = 15
DB_SQL_SCHEMA_FILE_NAME = "db_schema.sql"

# Maximum time in seconds to be blocked, waiting to acquire a db connection
# from the database connection pool.
DB_POOL_BLOCK_TIMEOUT = 5

# Maximum size of the internal queue of the thread pool. Once that size is
# reached, the main thread will block trying to put a new message in the
# thread pool until a thread finishes its work.
THREAD_POOL_QUEUE_MAX_SIZE = 300

# Maximum number of threads to be created in the thread pool. Change it to
# use a threads count different from the default. The default to be created is
# (os.cpu_count() or 1) * 5
THREAD_POOL_MAX_WORKERS = (os.cpu_count() or 1) * 5

# Maximum time in seconds to be blocked, waiting for a free slot in the
# Thread Pool's internal queue. This will be the maximum time, that the main
# thread will be waiting to put a website's metrics in the ThreadPool to be
# processed, when the thread pool's internal queue size had increased to
# THREAD_POOL_QUEUE_MAX_SIZE. If the specified time elapses, the message will
# be discarded.
THREAD_POOL_BLOCK_TIMEOUT = 5

# Maximum time in milliseconds to wait blocked, to acquire new messages from
# the Kafka server when poll.
POLL_TIMEOUT_MS = 2000
CONSUMER_THREAD_NAME = "StreamConsumerThread"

DEFAULT_LOG_LEVEL = "DEBUG"
LOGGER_NAME = "root"
LOGGING: typing.Dict[str, typing.Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": logging.DEBUG,
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "loghandler": {
            "level": "",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "",
            "maxBytes": 1024 * 1024 * 2,  # 2Mb
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "formatters": {
        "verbose": {
            "format": "%(levelname)s|%(threadName)s|%(asctime)s|%(filename)s:%(lineno)s"
                      " - %(funcName)10s(): %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    # "loggers": {
    #     "root": {
    #         "handlers": ["loghandler", "console"],
    #         "level": "",
    #         "propagate": False
    #     }
    # },
    LOGGER_NAME: {
        "handlers": ["loghandler", "console"],
        "level": "",
        "propagate": False,
    },
}
