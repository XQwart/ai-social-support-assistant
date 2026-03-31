from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def build_url(base_url: str, params: dict[str, str | None]) -> str:
    parsed = urlsplit(base_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({key: value for key, value in params.items() if value is not None})

    return urlunsplit(parsed._replace(query=urlencode(query)))
