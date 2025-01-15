import json
from pathlib import Path
from typing import List


def read_json(filename: str):
    with Path(filename).open("w") as f_in:
        return json.load(f_in)


def write_json(filename: str, value):
    with Path(filename).open("w") as fp:
        json.dump(value, fp)


class StoreService:
    def get(self, key: str):
        """
        Get cached value if exists, else return None.

        :param key: cache_services key
        """
        raise NotImplementedError("Method is not implemented")

    def put(self, key: str, value):
        """
        Put object to cache_services.

        :param key: cache_services key
        :param value: cache_services value
        """
        raise NotImplementedError("Method is not implemented")


class InMemoryStoreService(StoreService):
    def __init__(self, cache=None, separator="."):
        if cache is None:
            cache = {}
        self.cache = cache
        self.separator = separator

    def get(self, key: str):
        """
        Get cached value if exists, else return None.

        :param key: cache_services key
        """

        if key not in self.cache.keys():
            return None

        return self.cache[key]

    def get_with_level(self, keys: List[str]):
        """
        Get JSON value by keys chain in 'keys' param.

        :param keys: keys chain param
        """

        key = self._create_key(keys)
        return self.get(key)

    def put(self, key: str, value):
        """
        Put object to cache_services.

        :param key: cache_services key
        :param value: cache_services value
        """

        self.cache[key] = value

    def put_with_level(self, keys: List[str], value):
        """
        Put JSON value by keys chain in 'keys' param.

        :param value: value to put
        :param keys: keys chain param
        """

        key = self._create_key(keys)
        self.put(key, value)

    def _create_key(self, keys: List[str]):
        return self.separator.join(keys)


class JsonStoreService(InMemoryStoreService):
    def __init__(self, filename="cache.json", separator="."):
        super().__init__(separator=separator)
        mem_cache = {}
        if Path(filename).is_file():
            mem_cache = read_json(filename)
        self.cache = mem_cache
        self.filename = filename
        self.separator = separator

    def put(self, key: str, value):
        """
        Put object to cache_services.

        :param key: cache_services key
        :param value: cache_services value
        """
        super().put(key, value)
        write_json(self.filename, self.cache)

    def put_with_level(self, keys: List[str], value):
        """
        Put JSON value by keys chain in 'keys' param.

        :param value: value to put
        :param keys: keys chain param
        """

        super().put_with_level(keys, value)
        write_json(self.filename, self.cache)


class FastStoreService(InMemoryStoreService):
    def flush(self):
        """
        Flush data to persisted store.
        """

        raise NotImplementedError("Method is not implemented")


class FastJsonStoreService(FastStoreService):
    def __init__(self, filename="cache.json", separator="."):
        super().__init__(separator=separator)
        mem_cache = {}
        if Path(filename).is_file():
            mem_cache = read_json(filename)
        self.cache = mem_cache
        self.filename = filename
        self.separator = separator

    def flush(self):
        """
        Flush data to persisted store.
        """

        write_json(self.filename, self.cache)
