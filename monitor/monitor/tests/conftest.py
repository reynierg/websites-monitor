import inspect
import os

import pytest

from monitor.monitor.utils import UrlsProviderFactory


@pytest.fixture
def monitor_test_base_dir():
    """Returns the monitor's tests directory path"""

    return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


@pytest.fixture
def csv_urls_provider(monitor_test_base_dir):
    """Instantiate a CsvUrlsProvider"""

    with UrlsProviderFactory.get_urls_provider(
        "CsvUrlsProvider",
        f"{monitor_test_base_dir}{os.sep}data{os.sep}urls.csv",
        logger_name=__name__,
    ) as urls_provider:

        yield urls_provider


@pytest.fixture
def json_urls_provider(monitor_test_base_dir):
    """Instantiate a JsonUrlsProvider"""

    with UrlsProviderFactory.get_urls_provider(
        "JsonUrlsProvider",
        f"{monitor_test_base_dir}{os.sep}data{os.sep}urls.json",
        logger_name=__name__,
    ) as urls_provider:

        yield urls_provider


@pytest.fixture
def expected_urls_in_json_file():
    """Returns the urls expected to exist in the JSON file"""

    return {
        "https://www.google.com",
        "https://realpython.com",
        "https://reynierdoesnotexistAGDBFHORU23523.com",
    }


@pytest.fixture
def expected_urls_in_csv_file():
    """Returns the urls expected to exist in the CSV file"""

    return {
        "https://www.google.com",
        "https://realpython.com",
        "https://reynierdoesnotexistAGDBFHORU23523.com",
    }


@pytest.fixture
def expected_regexp_in_json_file():
    """Returns the regexp patterns expected to exist in the JSON file"""

    return {"Gmail", "All Tutorial \\w+", "DOESNOTEXIST"}


@pytest.fixture
def expected_regexp_in_csv_file():
    """Returns the regexp patterns expected to exist in the CSV file"""

    return {"Gmail", "All Tutorial \\w+", "DOESNOTEXIST"}
