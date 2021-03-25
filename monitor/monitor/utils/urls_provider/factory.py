"""Contains logic to create a UrlsProvider

This file can be imported as a module and contains the following classes:
    * InvalidUrlsProviderException - Will be throw when the
        `UrlsProvider` type specified to be instantiated, is not recognized
    * UrlsProviderFactory - Provides an instance of the required
        `UrlsProvider`
"""

import importlib
import typing

from .urls_provider import UrlsProvider

CSV_URLS_PROVIDER_NAME = "CsvUrlsProvider"
JSON_URLS_PROVIDER_NAME = "JsonUrlsProvider"


IMPORT_INDEX = {
    CSV_URLS_PROVIDER_NAME: lambda: importlib.import_module(
        "monitor.monitor.utils.urls_provider.csv_urls_provider"
    ),
    JSON_URLS_PROVIDER_NAME: lambda: importlib.import_module(
        "monitor.monitor.utils.urls_provider.json_urls_provider"
    ),
}


class InvalidUrlsProviderException(Exception):
    """Exception to be thrown when the `UrlsProvider` type specified to be
    instantiated, is not recognized"""


class UrlsProviderFactory:
    """Provides an instance of the required UrlsProvider"""

    @staticmethod
    def get_urls_provider(
        urls_provider_type: str, resource_path: str, *args: typing.Tuple, **kwargs: dict
    ) -> UrlsProvider:
        """Returns an instance of the UrlsProvider required.

        Parameters
        ----------
        urls_provider_type : str
            Type of the urls provider to instantiate.
        resource_path : str
            Path of the resource to grab the urls from.
        args : typing.Tuple
            Additional arguments to be passed to the URlsProvider
        kwargs : dict
            Additional key-word arguments to be passed to the URlsProvider

        Returns
        -------
        StreamConsumer
            Concrete instance of the required URlsProvider.

        Raises
        ------
        InvalidUrlsProviderException
            If the specified urls_provider_type is not recognized.
        """

        import_statement = IMPORT_INDEX.get(urls_provider_type)
        if import_statement is None:
            raise InvalidUrlsProviderException(
                f"Specified urls_provider_type is invalid: " f"{urls_provider_type}"
            )

        urls_provider_class = getattr(import_statement(), urls_provider_type)

        return urls_provider_class(resource_path, *args, **kwargs)
