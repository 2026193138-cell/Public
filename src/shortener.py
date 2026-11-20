from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashTable


class UrlShortener:
    def __init__(self):
        self._url_to_code = HashTable()
        self._code_to_url = HashTable()
        self._next_id = 0

    @staticmethod
    def _validate_url(url):
        if not isinstance(url, str):
            raise ValueError("URL must be a string")

        url = url.strip()
        if not url:
            raise ValueError("URL must not be empty")
        if any(character.isspace() for character in url):
            raise ValueError("URL must not contain whitespace")

        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("URL must start with http:// or https://")
        return url

    def shorten(self, url):
        url = self._validate_url(url)

        if self._url_to_code.contains(url):
            return self._url_to_code.get(url)

        code = encode(self._next_id)
        self._next_id += 1
        self._url_to_code.put(url, code)
        self._code_to_url.put(code, url)
        return code

    def expand(self, code):
        if not isinstance(code, str) or not code:
            raise KeyError(code)
        return self._code_to_url.get(code)
