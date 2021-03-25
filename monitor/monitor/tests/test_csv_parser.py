def test_parse_csv_urls_file(
    csv_urls_provider, expected_urls_in_csv_file, expected_regexp_in_csv_file
):
    parsed_urls = set()
    parsed_regexp_list = set()
    for url_data in csv_urls_provider:
        parsed_urls.add(str(url_data.url))
        parsed_regexp_list.add(url_data.regexp)

    assert parsed_urls == expected_urls_in_csv_file
    assert parsed_regexp_list == expected_regexp_in_csv_file
