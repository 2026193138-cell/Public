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
            body = response.read().decode("utf-8")

        self.assertIn("Shorten URL", body)
        self.assertIn('type="reset"', body)
        self.assertIn('href="/table"', body)

    def test_shorten_accepts_valid_url(self):
        import urllib.parse
        import urllib.request

        data = urllib.parse.urlencode({"url": "https://example.com"}).encode()
        request = urllib.request.Request(f"{self.base_url}/shorten", data=data)

        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode("utf-8")
            self.assertIn("Short URL", body)
            self.assertIn("example.com", body)
            self.assertIn("Open short URL", body)
            self.assertIn("Shorten another", body)

    def test_short_url_redirects_to_original_url(self):
        import urllib.error
        import urllib.parse
        import urllib.request

        data = urllib.parse.urlencode({"url": "https://example.com/path"}).encode()
        request = urllib.request.Request(f"{self.base_url}/shorten", data=data)
        with urllib.request.urlopen(request) as response:
            body = response.read().decode("utf-8")

        code = body.split('data-code="', 1)[1].split('"', 1)[0]
        redirect_request = urllib.request.Request(
            f"{self.base_url}/{code}",
            method="GET",
        )
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, new_url):
                return None

        opener = urllib.request.build_opener(NoRedirectHandler)
        with self.assertRaises(urllib.error.HTTPError) as context:
            opener.open(redirect_request)

        self.assertEqual(context.exception.code, 302)
        self.assertEqual(
            context.exception.headers.get("Location"),
            "https://example.com/path",
        )

    def test_table_route_shows_hash_table_state(self):
        import urllib.request

        with urllib.request.urlopen(f"{self.base_url}/table") as response:
            body = response.read().decode("utf-8")

        self.assertIn("Hash Table", body)
        self.assertIn("Horner", body)
        self.assertIn("capacity", body)
        self.assertIn("Load factor", body)
        self.assertIn("Collision buckets", body)
        self.assertIn("Refresh", body)

    def test_table_route_renders_collisions_as_linked_list_nodes(self):
        import urllib.parse
        import urllib.request

        for url in ("https://example.com/a", "https://example.com/q"):
            data = urllib.parse.urlencode({"url": url}).encode()
            request = urllib.request.Request(f"{self.base_url}/shorten", data=data)
            with urllib.request.urlopen(request):
                pass

        with urllib.request.urlopen(f"{self.base_url}/table") as response:
            body = response.read().decode("utf-8")

        self.assertIn("collision", body.lower())
        self.assertIn("https://example.com/a", body)
        self.assertIn("https://example.com/q", body)
        self.assertIn("&rarr;", body)
        self.assertIn("NULL", body)

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
