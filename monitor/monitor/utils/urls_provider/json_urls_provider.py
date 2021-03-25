"""Contains logic to acquire urls from a JSON file

This file can be imported as a module and contains the following classes:
    * JsonUrlsProvider - Provides access to urls from a JSON file
"""

import io
import json
import os
import typing

import pydantic

from monitor.monitor.utils.models import UrlModel
from .file_urls_provider import FileUrlsProvider


class JsonUrlsProvider(FileUrlsProvider):
    """Provides access to urls from a JSON file

    Methods
    -------
    generator()
        Property that returns an urls generator. The urls will be generated
        one at a time when iterate over.
    _parse_json_documents()
        Yields one JSON document at a time from the input JSON file.
    _parse_text_line()
        Tries to parse from a string an url input record.
    """

    def __init__(self, file_path: str, *args, **kwargs):
        """

        Parameters
        ----------
        file_path : str
            Full path of the JSON file with the urls
        *args : typing.Tuple
            Non-keyworded variable-length argument
        **kwargs:
            Keyworded, variable-length arguments
        """

        super().__init__(file_path, *args, **kwargs)
        self._logger.debug("%s.__init__(...)", self.__class__.__name__)

    @property
    def generator(self) -> typing.Generator[typing.Optional[UrlModel], None, None]:
        self._logger.debug("%s.generator()", self.__class__.__name__)
        return self._parse_json_documents()

    def _parse_json_documents(
        self,
    ) -> typing.Generator[typing.Optional[UrlModel], None, None]:
        """Yields one line at a time from the input JSON file"""

        self._logger.debug("%s._parse_json_documents()", self.__class__.__name__)
        # The JSON file could be huge, so it must be parsed one line at a
        # time, for not get OutOfMemory exception:
        line_index = 1
        processed_json_documents_count = 0
        io_file = typing.cast(io.TextIOWrapper, self._file)
        for line in io_file:
            line = line.strip()
            self._logger.debug("Line '%s''s content after strip spaces:", line_index)
            self._logger.debug(line)

            if not line or line == os.linesep:
                self._logger.warning(
                    "Line '%s' is empty, it will be ignored", line_index
                )
                line_index += 1
                continue

            if line in ("]", f"]{os.linesep}"):
                self._logger.debug(
                    "The end of the file was found at line #'%s'", line_index
                )
                self._logger.info(
                    "In total, there were processed %s JSON documents",
                    processed_json_documents_count
                )
                return

            if line in ("[", f"[{os.linesep}"):
                self._logger.debug(
                    "The first line of the file was found at line #'%s'", line_index
                )
                line_index += 1
                continue

            try:
                # Looking for the index of the character that close a JSON
                # document definition:
                open_brace_idx = line.index("{")
                close_brace_idx = line.rindex("}")
                if open_brace_idx != 0:
                    self._logger.warning(
                        "Line #'%s' is malformed. The open curly brace "
                        "character '{' must be the first in the every line",
                        line_index
                    )
                    line_index += 1
                    continue
            except ValueError:
                # Line is malformed:
                self._logger.exception(
                    "Line #'%s' is malformed. Every JSON document should be "
                    "in its own line:",
                    line_index
                )
                line_index += 1
                continue

            # Ignore any character(including the ',' character) that appears
            # after the '}' character, at the end of the line:
            line = line[: close_brace_idx + 1]
            json_document: typing.Optional[UrlModel] = self._parse_text_line(
                line, line_index
            )
            line_index += 1
            if json_document is None:
                # Line doesn't contains a valid JSON document:
                continue

            # Process the Python dict with the JSON document data:
            yield json_document
            processed_json_documents_count += 1

    def _parse_text_line(self, line: str, line_index: int) \
            -> typing.Optional[UrlModel]:
        """Tries to parse from a string an url input record.

        It will first try to load a JSON document from the string, and then
        initialize a UrlModel with it.

        Parameters
        ----------
        line : str
            A string line that should contains a JSON document with an url
            data
        line_index : int
            Represents the base 0 index, of the string line in the input file

        Returns
        -------
        typing.Optional[UrlModel]
            If from the line could be loaded a JSON document and contains the
            expected fields, will be returned a UrlModel instance with the
            data.
            If not, None will be returned.
        """

        self._logger.debug("%s._parse_text_line(...)", self.__class__.__name__)
        try:
            # Deserialize a text line containing a JSON document, to a Python
            # dict:
            data = json.loads(line)
            # Validate the JSON document structure, and use the model to
            # access its content:
            return UrlModel(**data)
        except json.JSONDecodeError:
            self._logger.warning(
                "JSON document in line #'%s' is malformed. It will be ignored",
                line_index
            )
            return None
        except pydantic.ValidationError:
            self._logger.warning(
                "JSON document in line '%s' is invalid or malformed. It must "
                "contain all/just the expected fields. It will be ignored",
                line_index
            )
            return None
