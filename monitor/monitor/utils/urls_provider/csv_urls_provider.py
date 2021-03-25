"""Contains logic to acquire urls from a CSV file

This file can be imported as a module and contains the following classes:
    * CsvUrlsProvider - Provides access to urls from a CSV file
"""

import csv
import io
import typing

import pydantic

from .file_urls_provider import FileUrlsProvider
from ..models import UrlModel


class CsvUrlsProvider(FileUrlsProvider):
    """Provides access to urls from a CSV file

    Methods
    -------
    generator()
        Property that returns an urls generator. The urls will be generated
        one at a time when iterate over.
    _parse_csv_lines()
        Yields one line at a time from the input CSV file.
    _map_dict_to_model()
        Instantiate a model from a dict with an website's metadata.
    """

    URL_COLUMN_NAME = "url"
    REGEXP_COLUMN_NAME = "regexp"
    DELIMITER = ","

    def __init__(self, file_path: str, *args, **kwargs):
        """

        Parameters
        ----------
        file_path : str
            Full path of the CSV file with the urls
        *args : typing.Tuple
            Non-keyworded variable-length argument
        **kwargs:
            Keyworded, variable-length arguments
        """

        super().__init__(file_path, *args, **kwargs)
        self._logger.debug("%s.__init__(...)", self.__class__.__name__)
        self._regexp_column_name = kwargs.get(
            self.REGEXP_COLUMN_NAME, self.REGEXP_COLUMN_NAME
        )
        self._url_column_name = kwargs.get(self.URL_COLUMN_NAME, self.URL_COLUMN_NAME)
        self._delimiter = kwargs.get("delimiter", self.DELIMITER)

    @property
    def generator(self) -> typing.Generator[typing.Optional[UrlModel], None, None]:
        self._logger.debug("%s.generator()", self.__class__.__name__)
        return self._parse_csv_lines()

    def _parse_csv_lines(
        self,
    ) -> typing.Generator[typing.Optional[UrlModel], None, None]:
        """Yields one line at a time from the input CSV file."""

        self._logger.debug("%s._parse_csv_lines()", self.__class__.__name__)
        # The CSV file could be huge, so it must be parsed one line at a time,
        # for not get OutOfMemory exception:
        io_file = typing.cast(io.TextIOWrapper, self._file)
        csv_reader = csv.DictReader(io_file, delimiter=self._delimiter)
        line_index = 1
        processed_lines_count = 0
        for row in csv_reader:
            self._logger.debug("row: %s", row)
            data = {
                "url": row[self._url_column_name],
                "regexp": row[self._regexp_column_name],
            }
            url_model: typing.Optional[UrlModel] = self._map_dict_to_model(
                data, line_index
            )
            line_index += 1
            if url_model is None:
                # The row doesn't contains a valid url row:
                continue

            # Process the row with the url metadata:
            yield url_model
            processed_lines_count += 1

        self._logger.debug("The end of the file was found at line #'%s'", line_index)
        self._logger.info(
            "In total, there were processed %s urls rows",
            processed_lines_count,
        )

    def _map_dict_to_model(
        self, row: typing.Dict[str, str], line_index: int
    ) -> typing.Optional[UrlModel]:
        """Instantiate a model from a dict with an website's metadata.

        After validate the website's metadata, it will initialize a UrlModel
        with it.

        Parameters
        ----------
        row : typing.Dict[str, str]
            A dict that should contains an url related metadata
        line_index : int
            Represents the base 0 index, of the string line in the input file

        Returns
        -------
        typing.Optional[UrlModel]
            If from the line could be loaded a row and contains the expected
            fields, will be returned a UrlModel instance with the data.
            If not, None will be returned.
        """

        self._logger.debug("%s.__parse_row(...)", self.__class__.__name__)
        try:
            # Validate the row structure, and use the model to access its
            # content:
            return UrlModel(**row)
        except pydantic.ValidationError:
            self._logger.warning(
                "Row in line '%s' is invalid or malformed. It must contain "
                "all/just the expected fields. It will be ignored",
                line_index,
            )
            return None
