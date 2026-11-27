_EMPTY = object()
_DELETED = object()


class LinearProbingHashTable:
    def __init__(self, capacity=16):
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise ValueError("capacity must be a positive integer")
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")

        self.capacity = capacity
        self._slots = [_EMPTY] * capacity
        self._size = 0

    def __len__(self):
        return self._size

    @staticmethod
    def _hash(key):
        if not isinstance(key, str):
            raise TypeError("LinearProbingHashTable keys must be strings")

        value = 0
        for character in key:
            value = (value * 31 + ord(character)) & 0xFFFFFFFF
        return value

    def _find_slot(self, key):
        start = self._hash(key) % self.capacity
        first_deleted = None

        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            slot = self._slots[index]
            if slot is _EMPTY:
                return (first_deleted if first_deleted is not None else index), False
            if slot is _DELETED:
                if first_deleted is None:
                    first_deleted = index
            elif slot[0] == key:
                return index, True

        if first_deleted is not None:
            return first_deleted, False
        return None, False

    def contains(self, key):
        _, found = self._find_slot(key)
        return found

    def get(self, key):
        index, found = self._find_slot(key)
        if not found:
            raise KeyError(key)
        return self._slots[index][1]

    def put(self, key, value):
        self._hash(key)
        index, found = self._find_slot(key)
        if found:
            raise KeyError(key)

        if index is None:
            self._resize()
            index, found = self._find_slot(key)
        self._slots[index] = (key, value)
        self._size += 1

        if self._size / self.capacity > 0.75:
            self._resize()

    def delete(self, key):
        index, found = self._find_slot(key)
        if not found:
            raise KeyError(key)

        value = self._slots[index][1]
        self._slots[index] = _DELETED
        self._size -= 1
        return value

    def snapshot(self):
        result = []
        for bucket_index, slot in enumerate(self._slots):
            if slot is _EMPTY:
                result.append((bucket_index, "empty", None, None, None))
            elif slot is _DELETED:
                result.append((bucket_index, "deleted", None, None, None))
            else:
                key, value = slot
                result.append((bucket_index, "occupied", key, value, self._hash(key)))
        return result

    def probe_trace(self, key):
        start = self._hash(key) % self.capacity
        trace = []

        for offset in range(self.capacity):
            bucket_index = (start + offset) % self.capacity
            slot = self._slots[bucket_index]
            if slot is _EMPTY:
                trace.append((bucket_index, "empty"))
                break
            if slot is _DELETED:
                trace.append((bucket_index, "deleted"))
            elif slot[0] == key:
                trace.append((bucket_index, "found"))
                return trace
            else:
                trace.append((bucket_index, "collision"))

        raise KeyError(key)

    def _resize(self):
        old_slots = self._slots
        self.capacity *= 2
        self._slots = [_EMPTY] * self.capacity
        self._size = 0

        for slot in old_slots:
            if slot is not _EMPTY and slot is not _DELETED:
                index, _ = self._find_slot(slot[0])
                self._slots[index] = slot
                self._size += 1
