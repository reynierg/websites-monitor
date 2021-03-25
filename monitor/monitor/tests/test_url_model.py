import pydantic
import pytest

from monitor.monitor.utils.models import UrlModel


def test_invalid_url_model_url_is_none():
    error_msg = (
        r"1 validation error for UrlModel\nurl\n  none is not an "
        r"allowed value \(type=type_error.none.not_allowed\)"
    )
    with pytest.raises(pydantic.ValidationError, match=error_msg):
        url_metadata = {"url": None}
        model = UrlModel(**url_metadata)
        assert model


def test_invalid_url_model_url_is_empty():
    error_msg = (
        r"1 validation error for UrlModel\nurl\n  ensure this value "
        r"has at least 1 characters "
        r"\(type=value_error.any_str.min_length; limit_value=1\)"
    )
    with pytest.raises(pydantic.ValidationError, match=error_msg):
        url_metadata = {"url": ""}
        model = UrlModel(**url_metadata)
        assert model


def test_invalid_url_model_url_has_invalid_invalid_scheme():
    error_msg = (
        r"1 validation error for UrlModel\nurl\n  invalid or "
        r"missing URL scheme \(type=value_error.url.scheme\)"
    )
    with pytest.raises(pydantic.ValidationError, match=error_msg):
        url_metadata = {"url": "http"}
        model = UrlModel(**url_metadata)
        assert model


def test_valid_url_model_url_is_valid():
    url_metadata = {"url": "https://www.google.com"}
    model = UrlModel(**url_metadata)
    assert model


def test_valid_url_model_regexp_is_empty():
    url_metadata = {"url": "https://www.google.com", "regexp": ""}
    model = UrlModel(**url_metadata)
    assert model


def test_valid_url_model_regexp_is_none():
    url_metadata = {"url": "https://www.google.com", "regexp": None}
    model = UrlModel(**url_metadata)
    assert model
