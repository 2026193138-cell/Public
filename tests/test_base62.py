import unittest

from src.base62 import decode, encode


class Base62Test(unittest.TestCase):
    def test_encode_zero(self):
        self.assertEqual(encode(0), "0")

    def test_encode_known_values(self):
        cases = {
            10: "a",
            61: "Z",
            62: "10",
            3844: "100",
        }
        for number, encoded in cases.items():
            with self.subTest(number=number):
                self.assertEqual(encode(number), encoded)

    def test_decode_known_values(self):
        cases = {
            "0": 0,
            "a": 10,
            "Z": 61,
            "10": 62,
            "100": 3844,
        }
        for encoded, number in cases.items():
            with self.subTest(encoded=encoded):
                self.assertEqual(decode(encoded), number)

    def test_round_trip(self):
        for number in (0, 1, 61, 62, 123456789, 10**12):
            with self.subTest(number=number):
                self.assertEqual(decode(encode(number)), number)

    def test_negative_numbers_are_rejected(self):
        with self.assertRaises(ValueError):
            encode(-1)

    def test_invalid_characters_are_rejected(self):
        for encoded in ("", "_-", " 1", "1+"):
            with self.subTest(encoded=encoded):
                with self.assertRaises(ValueError):
                    decode(encoded)


if __name__ == "__main__":
    unittest.main()
