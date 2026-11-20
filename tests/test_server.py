import unittest

from src.server import create_server


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.server = create_server(host="127.0.0.1", port=0)
        self.server.start()
        self.base_url = f"http://127.0.0.1:{self.server.port}"

    def tearDown(self):
        self.server.stop()

    def test_root_is_available(self):
        import urllib.request

        with urllib.request.urlopen(f"{self.base_url}/") as response:
            self.assertEqual(response.status, 200)

    def test_shorten_accepts_valid_url(self):
        import urllib.parse
        import urllib.request

        data = urllib.parse.urlencode({"url": "https://example.com"}).encode()
        request = urllib.request.Request(f"{self.base_url}/shorten", data=data)

        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.status, 200)

    def test_shorten_rejects_missing_url(self):
        import urllib.error
        import urllib.parse
        import urllib.request

        data = urllib.parse.urlencode({}).encode()
        request = urllib.request.Request(f"{self.base_url}/shorten", data=data)

        with self.assertRaises(urllib.error.HTTPError) as context:
            urllib.request.urlopen(request)
        self.assertEqual(context.exception.code, 400)

    def test_unknown_code_returns_not_found(self):
        import urllib.error
        import urllib.request

        with self.assertRaises(urllib.error.HTTPError) as context:
            urllib.request.urlopen(f"{self.base_url}/missing")
        self.assertEqual(context.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
