"""Contains common logic to all urls providers

This file can be imported as a module and contains the following classes:
    * UrlsProvider - Provides access to urls from a data source.
"""

import abc
import logging
import types
import typing

from monitor.monitor.utils.models import UrlModel


class UrlsProvider(abc.ABC):
    """Provides access to urls from a data source.

    Contains functionality common to all urls providers.
    Define abstract methods/properties to be implemented by all urls
    providers.
    Implements a context manager and an iterable.

    Methods
    -------
    __enter__()
        Prepares the underlying urls data source to access the urls
    __exit__(exc_type, exc_val, exc_tb)
        Asks the underlying urls data source to close
    __iter__()
        Provides an urls iterator from the underlying urls provider
    generator()
        Concrete urls providers must supply an urls iterator
    allocate_resources()
        Concrete urls providers must prepare the urls data source
    deallocate_resources()
        Concrete urls providers must close the urls data source
    """

    def __init__(self, source: str, *args, **kwargs):
        """

        Parameters
        ----------
        source : str
            Source that contains the urls
        *args : typing.Tuple
            Non-keyworded variable-length argument
        **kwargs:
            Keyworded, variable-length arguments
        """

        # pylint: disable=unused-argument
        self._source = source
        logger_name = kwargs.get("logger_name", __name__)
        self._logger = logging.getLogger(logger_name)
        self._logger.debug(
            "UrlsProvider.__init__(source=%s, logger_name=%s)", source, logger_name
        )

    def __enter__(self) -> "UrlsProvider":
        """Prepares the underlying urls data source to access the urls.

        Returns
        -------
        UrlsProvider
            Returns an instance of this class being used as a context manager.
        """

        self._logger.debug("UrlsProvider.__enter__(...)")
        self.allocate_resources()
        return self

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ):
        """Asks the underlying urls data source to close.

        Parameters
        ----------
        exc_type : typing.Optional[typing.Type[BaseException]]
            Type of the exception that caused the context to be exited
        exc_val : typing.Optional[BaseException]
            The exception that caused the context to be exited
        exc_tb : typing.Optional[types.TracebackType]
            Traceback related to the call stack associated to the exception
        """

        self._logger.debug("UrlsProvider.__exit__(...)")
        self.deallocate_resources()

    def __iter__(self) -> typing.Generator[typing.Optional[UrlModel], None, None]:
        """Provides an urls iterator from the underlying urls provider

        Returns
        -------
        Iterator
            Iterator that generates urls
        """

        self._logger.debug("UrlsProvider.__iter__(...)")
        return self.generator

    @property
    @abc.abstractmethod
    def generator(self) -> typing.Generator[typing.Optional[UrlModel], None, None]:
        """Concrete urls providers must supply an urls iterator"""

    @abc.abstractmethod
    def allocate_resources(self):
        """Concrete urls providers must prepare the urls data source"""

    @abc.abstractmethod
    def deallocate_resources(self):
        """Concrete urls providers must close the urls data source"""
