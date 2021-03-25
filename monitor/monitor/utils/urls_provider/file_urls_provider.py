"""Contains common logic to all file urls providers

This file can be imported as a module and contains the following classes:
    * FileUrlsProvider - Provides common logic to all file urls providers
"""

from abc import ABC
import io
import typing

from .urls_provider import UrlsProvider


class FileUrlsProvider(UrlsProvider, ABC):
    """Provides common logic to all file urls providers

    Methods
    -------
    allocate_resources()
        Opens the file that contains the urls
    deallocate_resources()
        Closes the file that contains the urls
    """

    def __init__(self, file_path: str, *args, **kwargs):
        """

        Parameters
        ----------
        file_path : str
            Full path of the file with the urls
        *args : typing.Tuple
            Non-keyworded variable-length argument
        **kwargs:
            Keyworded, variable-length arguments
        """

        super().__init__(file_path, *args, **kwargs)
        self._logger.debug("FileUrlsProvider.__init__(file_path=%s)", file_path)
        self._file: typing.Optional[io.IOBase] = None

    def allocate_resources(self):
        """Opens the file that contains the urls."""

        self._logger.debug("FileUrlsProvider.allocate_resources(...)")
        self._file = open(self._source)

    def deallocate_resources(self):
        """Closes the file that contains the urls."""

        self._logger.debug("FileUrlsProvider.disconnect(...)")
        self._file.close()
        self._logger.info("The file '%s' was successfully closed", self._source)
