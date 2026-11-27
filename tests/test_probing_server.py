import unittest
import urllib.error
import urllib.parse
import urllib.request

from src.probing_server import create_server


class ProbingServerTest(unittest.TestCase):
    def setUp(self):
        self.server = create_server(host="127.0.0.1", port=0)
        self.server.start()
        self.base_url = f"http://127.0.0.1:{self.server.port}"

    def tearDown(self):
        self.server.stop()

    def _insert(self, data):
        body = urllib.parse.urlencode({"data": data}).encode()
        request = urllib.request.Request(f"{self.base_url}/insert", data=body)
        return urllib.request.urlopen(request)

    def test_root_offers_separate_views_and_shared_test_data_input(self):
        with urllib.request.urlopen(self.base_url) as response:
            body = response.read().decode()

        self.assertIn('action="/insert"', body)
        self.assertIn('href="/chaining"', body)
        self.assertIn('href="/linear-probing"', body)
        self.assertIn('href="/compare"', body)

    def test_same_test_data_is_visible_in_both_tables(self):
        with self._insert("a=first\nq=second"):
            pass

        with urllib.request.urlopen(f"{self.base_url}/compare") as response:
            body = response.read().decode()

        self.assertIn("Separate Chaining", body)
        self.assertIn("Linear Probing", body)
        self.assertGreaterEqual(body.count("<code>a</code>"), 2)
        self.assertGreaterEqual(body.count("<code>q</code>"), 2)

    def test_linear_view_shows_hash_storage_and_probe_path(self):
        with self._insert("a=first\nq=second"):
            pass

        with urllib.request.urlopen(f"{self.base_url}/linear-probing") as response:
            body = response.read().decode()

        self.assertIn("hash 113", body)
        self.assertIn("home bucket 1", body)
        self.assertIn("stored at bucket 2", body)
        self.assertIn("collision", body.lower())
        self.assertIn("bucket 1", body)
        self.assertIn("bucket 2", body)

    def test_chaining_view_remains_available(self):
        with self._insert("a=first\nq=second"):
            pass

        with urllib.request.urlopen(f"{self.base_url}/chaining") as response:
            body = response.read().decode()

        self.assertIn("Separate Chaining", body)
        self.assertIn("hash 97 % 16 = bucket 1", body)
        self.assertIn("hash 113 % 16 = bucket 1", body)
        self.assertIn("<code>a</code>", body)
        self.assertIn("<code>q</code>", body)

    def test_duplicate_batch_is_rejected_without_partial_insert(self):
        with self._insert("a=first"):
            pass

        body = urllib.parse.urlencode({"data": "b=second\na=duplicate"}).encode()
        request = urllib.request.Request(f"{self.base_url}/insert", data=body)
        with self.assertRaises(urllib.error.HTTPError) as context:
            urllib.request.urlopen(request)
        self.assertEqual(context.exception.code, 400)

        with urllib.request.urlopen(f"{self.base_url}/compare") as response:
            compare_body = response.read().decode()
        self.assertNotIn("<code>b</code>", compare_body)


if __name__ == "__main__":
    unittest.main()
