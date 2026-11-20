import unittest

from src.hash_table import HashTable


class HashTableTest(unittest.TestCase):
    def test_empty_table(self):
        table = HashTable()

        self.assertEqual(table.capacity, 16)
        self.assertEqual(len(table), 0)
        self.assertFalse(table.contains("missing"))

    def test_put_get_and_delete(self):
        table = HashTable()

        table.put("name", "Copilot")

        self.assertTrue(table.contains("name"))
        self.assertEqual(table.get("name"), "Copilot")
        self.assertEqual(table.delete("name"), "Copilot")
        self.assertFalse(table.contains("name"))

    def test_duplicate_key_is_rejected(self):
        table = HashTable()

        table.put("key", "first")

        with self.assertRaises(KeyError):
            table.put("key", "second")

    def test_missing_key_is_rejected(self):
        table = HashTable()

        with self.assertRaises(KeyError):
            table.get("missing")
        with self.assertRaises(KeyError):
            table.delete("missing")

    def test_collision_items_remain_reachable(self):
        table = HashTable(capacity=2)

        table.put("a", 1)
        table.put("b", 2)
        table.put("c", 3)

        self.assertEqual(table.get("a"), 1)
        self.assertEqual(table.get("b"), 2)
        self.assertEqual(table.get("c"), 3)

    def test_resize_rehashes_existing_items(self):
        table = HashTable(capacity=4)

        for number in range(20):
            table.put(f"key-{number}", number)

        self.assertGreater(table.capacity, 4)
        for number in range(20):
            self.assertEqual(table.get(f"key-{number}"), number)


if __name__ == "__main__":
    unittest.main()
