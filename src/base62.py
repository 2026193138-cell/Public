CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_BASE = len(CHARSET)


def encode(number: int) -> str:
    if isinstance(number, bool) or not isinstance(number, int):
        raise ValueError("number must be a non-negative integer")
    if number < 0:
        raise ValueError("number must be non-negative")
    if number == 0:
        return "0"

    encoded = []
    while number:
        number, remainder = divmod(number, _BASE)
        encoded.append(CHARSET[remainder])
    return "".join(reversed(encoded))


def decode(code: str) -> int:
    if not isinstance(code, str) or not code:
        raise ValueError("code must be a non-empty string")

    number = 0
    for character in code:
        if character not in CHARSET:
            raise ValueError("code contains an invalid character")
        number = number * _BASE + CHARSET.index(character)
    return number
