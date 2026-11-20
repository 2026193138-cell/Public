import unittest

from src.shortener import UrlShortener


class UrlShortenerTest(unittest.TestCase):
    def test_shorten_and_expand(self):
        shortener = UrlShortener()

        code = shortener.shorten("https://example.com")

        self.assertEqual(code, "0")
        self.assertEqual(shortener.expand(code), "https://example.com")

    def test_duplicate_url_returns_same_code(self):
        shortener = UrlShortener()

        first = shortener.shorten("https://example.com")
        second = shortener.shorten("https://example.com")

        self.assertEqual(first, second)

    def test_different_urls_get_different_codes(self):
        shortener = UrlShortener()

        first = shortener.shorten("https://one.example")
        second = shortener.shorten("https://two.example")

        self.assertNotEqual(first, second)
        self.assertEqual(shortener.expand(first), "https://one.example")
        self.assertEqual(shortener.expand(second), "https://two.example")

    def test_invalid_urls_are_rejected(self):
        shortener = UrlShortener()

        for url in ("", "   ", "example.com", "ftp://example.com", "https://exa mple.com"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shortener.shorten(url)

    def test_unknown_code_is_rejected(self):
        shortener = UrlShortener()

        with self.assertRaises(KeyError):
            shortener.expand("missing")


if __name__ == "__main__":
    unittest.main()
