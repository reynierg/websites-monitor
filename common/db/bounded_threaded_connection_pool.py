"""Provides functionality to manage a bounded database connections pool.

Inspired on the solution given on StackOverflow by "Rune Lyngsoe" using a
Semaphore. Added some tweaks, such that the calling thread will not be
waiting forever, the wait for a database connection will be aborted, if abort
is required. Also was included the use of threading.Event to handle abort
requests.
References:
    Python Postgres psycopg2 ThreadedConnectionPool exhausted
    https://stackoverflow.com/questions/48532301/python-postgres-psycopg2-threadedconnectionpool-exhausted

This file can be imported as a module and contains the following classes:
    * AbortException - Exception to be raised when abort is requested.
    * BoundedThreadedConnectionPool - Implements a workaround for
        "connection pool exhausted" error
"""

import logging
from threading import Event, Semaphore


class AbortException(Exception):
    """Exception to be raised when abort is requested"""


class BoundedThreadedConnectionPool:
    """Implements a workaround for "connection pool exhausted" error

    In the implementation of ThreadedConnectionPool, when the maxconn is
    reached and all connections are in use, if a thread tries to acquire a
    new connection an exception is raised with the error message "connection
    pool exhausted". This class prevent this behavior using a Semaphore
    instead, such that the calling thread will be blocked, until either: a
    connection is available or is asked to the connections pool to notify all
    waiting threads to abort execution.

    Methods
    -------
    getconn(key=None)
        Gets a connection from the db connections pool
    putconn(conn=None, key=None, close=False):
        Put away an unused connection
    abort()
        Alerts threads waiting for a db connection to abort their attempt
    """

    def __init__(self, threaded_connection_pool, block_timeout, logger_name=__name__):
        self._threaded_connection_pool = threaded_connection_pool
        self._block_timeout = block_timeout
        self._semaphore: Semaphore = Semaphore(self._threaded_connection_pool.maxconn)
        self._abort_event: Event = Event()
        self._logger: logging.Logger = logging.getLogger(logger_name)
        self._logger.debug(
            "%s.__init__(minconn=%s, maxconn=%s, block_timeout=%s, logger_name=%s)",
            self.__class__.__name__,
            self._threaded_connection_pool.minconn,
            self._threaded_connection_pool.maxconn,
            self._block_timeout,
            logger_name,
        )

    def getconn(self, key=None):
        """Gets a connection from the db connections pool.

        The calling thread will remain blocked until it either acquires a
        connection, or is informed to abort its attempt.

        Raises
        ------
        AbortException
            If the calling thread is informed to abort its attempt(when
            called the abort() method in this class)
        """

        self._logger.debug("%s.getconn()", self.__class__.__name__)
        # Handle graceful shutdown while waiting to acquire a db connection:
        while True:
            acquired = self._semaphore.acquire(
                blocking=True, timeout=self._block_timeout
            )
            if acquired:
                self._logger.debug("The semaphore was successfully acquired!")
                break

            self._logger.debug(
                "Failed to acquire the semaphore in %s seconds", self._block_timeout
            )
            # Sleep for 1 second before trying again to acquire the semaphore:
            if self._abort_event.wait(1):
                msg = (
                    "Aborting semaphore acquisition, abort event was "
                    "signaled by other thread!!!"
                )
                self._logger.warning(msg)
                raise AbortException(msg)

        try:
            return self._threaded_connection_pool.getconn(key=key)
        except Exception as ex:
            self._semaphore.release()
            self._logger.debug("The semaphore was successfully released!")
            raise ex

    def putconn(self, conn=None, key=None, close=False):
        """Put away an unused connection.

        If the connection is successfully released, it will release also the
        semaphore, so that other thread waiting blocked for a connection can
        acquired it.
        """

        self._logger.debug("%s.putconn()", self.__class__.__name__)
        self._threaded_connection_pool.putconn(conn=conn, key=key, close=close)
        self._semaphore.release()
        self._logger.debug("The semaphore was successfully released!")

    def closeall(self):
        """Close all connections (even the one currently in use.)"""

        self._logger.debug("%s.closeall()", self.__class__.__name__)
        self._threaded_connection_pool.closeall()

    def abort(self):
        """Alerts threads waiting for a db connection to abort their attempt"""

        self._logger.debug("%s.abort()", self.__class__.__name__)
        self._abort_event.set()
