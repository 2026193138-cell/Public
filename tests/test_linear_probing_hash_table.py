import unittest

from src.linear_probing_hash_table import LinearProbingHashTable


class LinearProbingHashTableTest(unittest.TestCase):
    def test_empty_table_and_basic_operations(self):
        table = LinearProbingHashTable()

        self.assertEqual(table.capacity, 16)
        self.assertEqual(len(table), 0)
        self.assertFalse(table.contains("missing"))

        table.put("name", "Copilot")

        self.assertTrue(table.contains("name"))
        self.assertEqual(table.get("name"), "Copilot")
        self.assertEqual(table.delete("name"), "Copilot")
        self.assertFalse(table.contains("name"))

    def test_duplicate_key_is_rejected(self):
        table = LinearProbingHashTable()
        table.put("key", "first")

        with self.assertRaises(KeyError):
            table.put("key", "second")

        self.assertEqual(table.get("key"), "first")

    def test_collisions_wrap_around_and_survive_deletion(self):
        table = LinearProbingHashTable(capacity=4)
        # These keys have the same initial bucket with the table's stable hash.
        table.put("c", 1)
        table.put("g", 2)
        table.put("k", 3)

        self.assertEqual(table.get("c"), 1)
        self.assertEqual(table.get("g"), 2)
        self.assertEqual(table.get("k"), 3)
        self.assertEqual(table.delete("g"), 2)
        self.assertEqual(table.get("k"), 3)

        table.put("o", 4)
        self.assertEqual(table.get("o"), 4)
        self.assertEqual(table.get("k"), 3)

    def test_resize_rehashes_existing_items(self):
        table = LinearProbingHashTable()

        for number in range(13):
            table.put(f"key-{number}", number)

        self.assertEqual(table.capacity, 32)
        for number in range(13):
            self.assertEqual(table.get(f"key-{number}"), number)

    def test_snapshot_and_probe_trace_show_hash_and_collision_path(self):
        table = LinearProbingHashTable()
        table.put("a", "first")
        table.put("q", "second")

        occupied = [slot for slot in table.snapshot() if slot[1] == "occupied"]
        self.assertIn((1, "occupied", "a", "first", 97), occupied)
        self.assertIn((2, "occupied", "q", "second", 113), occupied)
        self.assertEqual(
            table.probe_trace("q"),
            [(1, "collision"), (2, "found")],
        )

    def test_missing_keys_and_invalid_arguments(self):
        table = LinearProbingHashTable()

        with self.assertRaises(KeyError):
            table.get("missing")
        with self.assertRaises(KeyError):
            table.delete("missing")
        with self.assertRaises(TypeError):
            table.put(1, "value")
        with self.assertRaises(ValueError):
            LinearProbingHashTable(capacity=0)


if __name__ == "__main__":
    unittest.main()
