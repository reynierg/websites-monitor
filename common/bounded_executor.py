"""Provides functionality to manage a bounded Thread pool executor.

Inspired on the solution given on BetterCodeBytes by "Frank Cleary" using a
Semaphore to restrict how many work items can be hold in the internal queue.
Once the specified bound is reached, the thread calling "submit" will block
until the amount of work items in the queue decreases to less than the
specified bound. Added some tweaks, such that the calling thread will block
only for a predefined timeout, in which case will abort to enqueue the work
item, and will get rid of it.
References:
    TheadPoolExecutor with a bounded queue in Python
    https://www.bettercodebytes.com/theadpoolexecutor-with-a-bounded-queue-in-python/

This file can be imported as a module and contains the following classes:
    * BoundedExecutor - Enforces a bound for the standard ThreadPoolExecutor
        implementation
"""


from concurrent.futures import ThreadPoolExecutor
import logging
from threading import BoundedSemaphore
import typing


class BoundedExecutor:
    """Enforces a bound for the standard ThreadPoolExecutor implementation

    BoundedExecutor behaves as a ThreadPoolExecutor which will block on
    calls to submit() once the limit given as "bound" work items are queued
    for execution. This prevents overflow the job queue that is inside a the
    pool.

    Methods
    -------
    submit(fn, *args, **kwargs)
        Submits a callable to be executed with the given arguments.
    shutdown(wait=True)
        Clean-up the resources associated with the Executor.
    """

    def __init__(
        self,
        thread_pool_executor: ThreadPoolExecutor,
        bound: int,
        max_workers: int,
        block_timeout: int,
        logger_name: typing.Optional[str] = None,
    ):
        """Initializes a BoundedExecutor.

        Parameters
        ----------
        thread_pool_executor : ThreadPoolExecutor
            ThreadPoolExecutor to be bounded.
        bound : int
            The maximum number of work items in the work queue
        max_workers : int
            Maximum number of threads to be created in the thread pool
        block_timeout : int
            Maximum time in seconds to be blocked, waiting for a free slot in
            the Thread Pool's internal queue
        logger_name : typing.Optional[str] = None
            Logger's name
        """

        logger_name = logger_name or __name__
        self._logger = logging.getLogger(logger_name)
        self._logger.debug(
            "%s.__init__(bound=%s, max_workers=%s, block_timeout=%s, "
            "logger_name=%s)",
            self.__class__.__name__,
            bound,
            max_workers,
            block_timeout,
            logger_name,
        )
        self._executor: ThreadPoolExecutor = thread_pool_executor
        self._semaphore = BoundedSemaphore(bound + max_workers)
        self._block_timeout = block_timeout

    def _release_semaphore(self):
        """Releases the semaphore when a work item has been processed.

        This will reflect how many slots in the queue are in use.
        """

        self._logger.debug("%s._release_semaphore()", self.__class__.__name__)
        self._semaphore.release()
        self._logger.debug("The semaphore was successfully released!")

    def submit(self, call_back, *args, **kwargs):
        """Submits a callable to be executed with the given arguments.

        If the thread pool's queue has reached the specified bound, the
        calling thread will block for block_timeout, until a previous work
        item is processed. If the specified time elapses, the work item will
        be discarded.

        Parameters
        ----------
        call_back : typing.Callable
            Function to be executed by a thread pool's thread, with the
            arguments *args and **kwargs
        args : typing.Tuple
            Positional arguments to be passed to the function 'fn' when
            invoked
        kwargs : typing.Dict
            Named arguments to be passed to the function 'fn' when invoked
        """

        self._logger.debug("%s.submit()", self.__class__.__name__)
        acquired = self._semaphore.acquire(blocking=True, timeout=self._block_timeout)
        if not acquired:
            # Drops the message, if we are unable to acquire the semaphore
            # after self._block_timeout lapses, we don't want the calling
            # thread to be waiting indefinitely for a free slot in the
            # internal queue:
            self._logger.warning(
                "Maximum time to wait for a free slot has elapsed: %s",
                self._block_timeout,
            )
            return None

        self._logger.debug("The semaphore was successfully acquired!")
        try:
            future = self._executor.submit(call_back, *args, **kwargs)
        except RuntimeError as ex:
            self._semaphore.release()
            self._logger.debug("The semaphore was successfully released!")
            raise ex
        else:
            future.add_done_callback(lambda x: self._release_semaphore())
            return future

    def shutdown(self, wait=True):
        """Clean-up the resources associated with the Executor.

        Parameters
        ----------
        wait : bool
            If True then shutdown will not return until all running futures
            have finished executing and the resources used by the executor
            have been reclaimed.
        """

        self._logger.debug("%s.shutdown()", self.__class__.__name__)
        self._executor.shutdown(wait)
