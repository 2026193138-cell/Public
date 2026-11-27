class HashTable:
    def __init__(self, capacity=16):
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise ValueError("capacity must be a positive integer")
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")

        self.capacity = capacity
        self._buckets = [[] for _ in range(capacity)]
        self._size = 0

    def __len__(self):
        return self._size

    @staticmethod
    def _hash(key):
        if not isinstance(key, str):
            raise TypeError("HashTable keys must be strings")

        value = 0
        for character in key:
            value = (value * 31 + ord(character)) & 0xFFFFFFFF
        return value

    def _index(self, key):
        return self._hash(key) % self.capacity

    def contains(self, key):
        bucket = self._buckets[self._index(key)]
        return any(existing_key == key for existing_key, _ in bucket)

    def get(self, key):
        bucket = self._buckets[self._index(key)]
        for existing_key, value in bucket:
            if existing_key == key:
                return value
        raise KeyError(key)

    def put(self, key, value):
        bucket = self._buckets[self._index(key)]
        for index, (existing_key, _) in enumerate(bucket):
            if existing_key == key:
                raise KeyError(key)

        bucket.append((key, value))
        self._size += 1
        if self._size / self.capacity > 0.75:
            self._resize()

    def delete(self, key):
        bucket = self._buckets[self._index(key)]
        for index, (existing_key, value) in enumerate(bucket):
            if existing_key == key:
                del bucket[index]
                self._size -= 1
                return value
        raise KeyError(key)

    def snapshot(self):
        result = []
        for bucket_index, bucket in enumerate(self._buckets):
            chain = []
            for key, value in bucket:
                chain.append((key, value, self._hash(key)))
            result.append((bucket_index, chain))
        return result

    def _resize(self):
        old_buckets = self._buckets
        self.capacity *= 2
        self._buckets = [[] for _ in range(self.capacity)]

        old_size = self._size
        self._size = 0
        for bucket in old_buckets:
            for key, value in bucket:
                self._buckets[self._index(key)].append((key, value))
                self._size += 1

        if self._size != old_size:
            raise RuntimeError("rehashing changed the table size")
