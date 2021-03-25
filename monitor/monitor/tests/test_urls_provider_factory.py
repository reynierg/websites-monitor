import pytest

from monitor.monitor.utils import CsvUrlsProvider
from monitor.monitor.utils import JsonUrlsProvider
from monitor.monitor.utils import InvalidUrlsProviderException
from monitor.monitor.utils import UrlsProviderFactory


def test_create_csv_urls_provider(csv_urls_provider):
    assert isinstance(csv_urls_provider, CsvUrlsProvider)


def test_create_json_urls_provider(json_urls_provider):
    assert isinstance(json_urls_provider, JsonUrlsProvider)


def test_create_invalid_urls_provider():
    invalid_urls_provider_name = "InvalidUrlsProvider"
    except_msg = (
        f"Specified urls_provider_type is invalid: " f"{invalid_urls_provider_name}"
    )
    with pytest.raises(InvalidUrlsProviderException, match=except_msg):
        UrlsProviderFactory.get_urls_provider(
            invalid_urls_provider_name,
            "Whatever here it will fail",
            logger_name=__name__,
        )
