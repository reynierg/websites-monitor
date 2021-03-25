# pylint: disable=missing-function-docstring

from concurrent.futures import ThreadPoolExecutor
import typing
from unittest import mock

from common.bounded_executor import BoundedExecutor


def create_bounded_pool_executor(
    bound, max_workers, block_timeout
) -> typing.Tuple[mock.MagicMock, BoundedExecutor]:
    """Creates a mocked thread pool and a bounded executor"""

    mock_pool_executor = mock.create_autospec(
        ThreadPoolExecutor, max_workers=max_workers
    )
    return mock_pool_executor, BoundedExecutor(
        mock_pool_executor,
        bound=bound,
        max_workers=max_workers,
        block_timeout=block_timeout,
    )


def test_thread_pool_submit_success():
    """A bounded executor should call the underlying submit method"""

    mock_pool_executor, bounded_executor = create_bounded_pool_executor(
        bound=2, max_workers=2, block_timeout=2
    )

    def thread_func():
        pass

    test_data = ("test_data",)
    future = bounded_executor.submit(thread_func, test_data)
    assert future is not None
    mock_pool_executor.submit.assert_called_once_with(thread_func, test_data)


def test_thread_pool_submit_fails_when_bound_is_reached():
    bound = 2
    max_workers = 2
    mock_pool_executor, bounded_executor = create_bounded_pool_executor(
        bound=bound, max_workers=max_workers, block_timeout=2
    )

    def thread_func():
        pass

    test_data = ("test_data",)
    for _ in range(max_workers + bound):
        bounded_executor.submit(thread_func, test_data)

    future = bounded_executor.submit(thread_func, test_data)
    assert (
        mock_pool_executor.submit.call_count == max_workers + bound
    ), f"'submit' should have been called {max_workers + bound} times by now"

    assert future is None


def test_thread_pool_shutdown_is_called():
    mock_pool_executor, bounded_executor = create_bounded_pool_executor(
        bound=2, max_workers=2, block_timeout=2
    )
    bounded_executor.shutdown()
    mock_pool_executor.shutdown.assert_called_once_with(True)
