"""Provides functionality that suppresses SIGINT & SIGTERM signal handlers
for a block of code.

Implementation is attributed to "Petr Beneš". Added some tweaks for change
prints by logs and other changes such that it works with Python 3.6. Also
added documentation.
References:
     Holy grail of graceful shutdown in Python
     https://github.com/wbenny/python-graceful-shutdown

This file can be imported as a module and contains the following classes:
    * DelayedKeyboardInterrupt - Context manager that suppresses SIGINT &
        SIGTERM signal handlers for a block of code.

"""

import logging
import os
import signal


__all__ = [
    "SIGNAL_TRANSLATION_MAP",
]

SIGNAL_TRANSLATION_MAP = {
    signal.SIGINT: "SIGINT",
    signal.SIGTERM: "SIGTERM",
}


class DelayedKeyboardInterrupt:
    """Context manager that suppresses SIGINT & SIGTERM signal handlers for a
    block of code.
    """

    def __init__(self, propagate_to_forked_processes=None, logger_name=__name__):
        """Constructs a context manager that suppresses SIGINT & SIGTERM
        signal handlers for a block of code.

        The signal handlers are called on exit from the block.
        Inspired by: https://stackoverflow.com/a/21919644
        Parameters
        ----------
        propagate_to_forked_processes : bool
            This parameter controls behavior of this context manager in forked
            processes.
            If True, this context manager behaves the same way in forked
            processes as in parent process.
            If False, signals received in forked processes are handled by the
            original signal handler.
            If None, signals received in forked processes are ignored
            (default).
        """
        self._pid = os.getpid()
        self._propagate_to_forked_processes = propagate_to_forked_processes
        self._sig = None
        self._frame = None
        self._old_signal_handler_map = None
        self._logger = logging.getLogger(logger_name)
        self._logger.debug("%s.__init__()", self.__class__.__name__)

    def __enter__(self):
        """Replaces the signal handlers associated with SIGINT and SIGTERM.

        The signal handlers are replaced with one that suppresses the signals
        in a code block
        """

        self._logger.debug("%s.__enter__()", self.__class__.__name__)
        self._old_signal_handler_map = {
            sig: signal.signal(sig, self._handler)
            for sig, _ in SIGNAL_TRANSLATION_MAP.items()
        }

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restores the previously replaced signal handlers.

        If a signal occurred, the original signal handler will be executed.
        """

        self._logger.debug("%s.__exit__()", self.__class__.__name__)
        for sig, handler in self._old_signal_handler_map.items():
            signal.signal(sig, handler)

        if self._sig is None:
            return

        self._old_signal_handler_map[self._sig](self._sig, self._frame)

    def _handler(self, sig, frame):
        """Stores the signal that occurred as well as the stack frame."""

        self._logger.debug("%s._handler()", self.__class__.__name__)
        self._sig = sig
        self._frame = frame

        #
        # Protection against fork.
        #
        if os.getpid() != self._pid:
            if self._propagate_to_forked_processes is False:
                self._logger.info(
                    "!!! DelayedKeyboardInterrupt._handler: %s received; "
                    "PID mismatch: os.getpid()=%s, self._pid=%s, calling "
                    "original handler",
                    SIGNAL_TRANSLATION_MAP[sig],
                    os.getpid(),
                    self._pid,
                )
                self._old_signal_handler_map[self._sig](self._sig, self._frame)
            elif self._propagate_to_forked_processes is None:
                self._logger.info(
                    "!!! DelayedKeyboardInterrupt._handler: %s received; "
                    "PID mismatch: os.getpid()=%s, ignoring the signal",
                    SIGNAL_TRANSLATION_MAP[sig],
                    os.getpid(),
                )
                return
            # elif self._propagate_to_forked_processes is True:
            #   ... passthrough

        self._logger.info(
            "!!! DelayedKeyboardInterrupt._handler: %s received; delaying "
            "KeyboardInterrupt",
            SIGNAL_TRANSLATION_MAP[sig],
        )
