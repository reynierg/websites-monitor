# pylint: disable=missing-function-docstring

import threading
import time
import typing
from unittest import mock

from psycopg2.pool import ThreadedConnectionPool

from common.db.bounded_threaded_connection_pool import BoundedThreadedConnectionPool


class ThreadedConnectionPoolForTest(ThreadedConnectionPool):
    """This is required for that 'create_autospec' doesn't throw an exception,
    because of minconn and maxconn being used before being created in the
    class constructor"""

    minconn = 1
    maxconn = 2


def create_bounded_connection_pool(
    min_conn, max_conn, block_timeout
) -> typing.Tuple[mock.MagicMock, BoundedThreadedConnectionPool]:
    """Creates a mocked connection pool and a bounded connections pool"""

    mock_connection_pool = mock.create_autospec(
        ThreadedConnectionPoolForTest, spec_set=True, instance=True
    )
    mock_connection_pool.minconn = min_conn
    mock_connection_pool.maxconn = max_conn
    # Acquire a bounded connection pool:
    bounded_connection_pool = BoundedThreadedConnectionPool(
        mock_connection_pool, block_timeout=block_timeout
    )

    return mock_connection_pool, bounded_connection_pool


def create_bounded_connection_pool_and_hold_n_conns(
    min_conn, max_conn, block_timeout, num_of_conns_to_hold
) -> typing.Tuple[mock.MagicMock, BoundedThreadedConnectionPool, list]:
    """Creates a mocked connection pool and a bounded connections pool

    The specified count of connections will be hold
    """
    mock_connection_pool, bounded_connection_pool = create_bounded_connection_pool(
        min_conn=min_conn, max_conn=max_conn, block_timeout=block_timeout
    )

    # Hold the number of specified connections from the connections pool:
    conns = []
    for _ in range(num_of_conns_to_hold):
        conns.append(bounded_connection_pool.getconn())

    return mock_connection_pool, bounded_connection_pool, conns


def start_thread(conns_pool):
    """Starts a thread's execution and provides to it the connections pool"""

    def thread_func(connection_pool):
        conn = connection_pool.getconn()
        # time.sleep(0.5)
        connection_pool.putconn(conn)

    thread = threading.Thread(target=thread_func, args=(conns_pool,))
    thread.start()
    return thread


def test_getconn_success():
    """Tests that from a connections pool of 1 connection it can be acquired

    Also verifies that the getconn() and putconn() of the underlying object gets
    called
    """

    (
        mock_connection_pool,
        bounded_connection_pool,
        conns,
    ) = create_bounded_connection_pool_and_hold_n_conns(
        min_conn=1,
        max_conn=1,
        # While waiting for an available connection in the pool, will
        # verify every 1s, if abort was required:
        block_timeout=1,
        num_of_conns_to_hold=1,
    )

    mock_connection_pool.getconn.assert_called_once()
    conn = conns.pop()
    bounded_connection_pool.putconn(conn)
    mock_connection_pool.putconn.assert_called_once_with(conn, key=None, close=False)


def test_thread_blocks_until_conn_is_released():
    """Tests that a thread blocks when all connections are in use

    When all connections in the bounded connections pool are in use, a calling
    thread trying to acquire a connection, should block until one connection
    is released back.
    """

    # Hold all connections available in the pool, so that the next intent to
    # get a connection from the pool, will block the calling thread until one
    # connection is released:
    max_conn = 2
    (
        mock_connection_pool,
        bounded_connection_pool,
        conns,
    ) = create_bounded_connection_pool_and_hold_n_conns(
        min_conn=1,
        max_conn=max_conn,
        # While waiting for an available connection in the pool, will
        # verify every 1s, if abort was required:
        block_timeout=1,
        num_of_conns_to_hold=max_conn,
    )

    # Start a thread that will try to get a connection from the connections
    # pool. The thread to be started will block until a connection is
    # released back, because all connections are currently in use by the main
    # thread:
    thread = start_thread(bounded_connection_pool)

    # Release the GIL so that the just created thread can execute
    # immediately, it will block waiting for a connection:
    time.sleep(1)
    assert (
        thread.isAlive()
    ), "Created thread should still be waiting for a connection from the pool"

    # Release one connection to allow the created thread to unblock and get it:
    bounded_connection_pool.putconn(conns.pop())
    # The created thread should finish very fast, after get an available
    # connection from the connections pool, it will just release it back:
    thread.join(2)
    assert (
        mock_connection_pool.getconn.call_count == max_conn + 1
    ), f"'getconn' should have been called {max_conn + 1} times by now"

    # Created thread should already have finished:
    assert not thread.isAlive(), "Created thread should already have finished"
    assert (
        mock_connection_pool.putconn.call_count == 2
    ), "'putconn' should has been called 2 times by now"

    # Release the remaining connections being hold by the main thread:
    conns_length = len(conns)
    for _ in range(conns_length):
        bounded_connection_pool.putconn(conns.pop())

    assert (
        mock_connection_pool.putconn.call_count == max_conn + 1
    ), f"'putconn' should have been called {max_conn + 1} times by now"


def test_blocked_threads_aborts_when_required():
    """A blocked thread should abort, when so required by the connections pool

    When all the connections in a bounded connections pool are in use, the
    next intent to acquire a connection from it will block the calling thread
    until either, a connection is released or the connection pool is asked to
    notify all threads waiting for a connection to abort execution.
    """

    # Hold all connections available in the pool, so that the next intent to
    # get a connection from the pool, will block the calling thread until one
    # connection is released:
    max_conn = 2
    (
        mock_connection_pool,
        bounded_connection_pool,
        _,
    ) = create_bounded_connection_pool_and_hold_n_conns(
        min_conn=1,
        max_conn=max_conn,
        # While waiting for an available connection in the pool, will
        # verify every 1s, if abort was required:
        block_timeout=1,
        num_of_conns_to_hold=max_conn,
    )

    # Start 2 threads that will try to get a connection from the connections
    # pool. The threads to be started will block until a connection is
    # released back, because all connections are currently in use by the main
    # thread:
    threads = []
    for _ in range(2):
        threads.append(start_thread(bounded_connection_pool))

    # Release the GIL so that the just created threads can execute
    # immediately, they will block waiting for a connection:
    time.sleep(2)
    assert all(t.isAlive() for t in threads), (
        "All the created threads should still be waiting for a connection "
        "from the pool"
    )

    # Ask the connections pool no notify the created threads that are waiting
    # for a connection from the pool, to abort execution:
    bounded_connection_pool.abort()
    for thread in threads:
        thread.join(2)

    assert all(
        not t.isAlive() for t in threads
    ), "All created threads should have finished by now"

    assert (
        mock_connection_pool.getconn.call_count == max_conn
    ), "'getconn' should have been called only by the main execution thread"


def test_close_all():
    """A bounded thread connection pool should call the underlying  closeall
    method"""

    mock_connection_pool, bounded_connection_pool = create_bounded_connection_pool(
        min_conn=1, max_conn=2, block_timeout=1
    )

    bounded_connection_pool.closeall()
    mock_connection_pool.closeall.assert_called_once()
