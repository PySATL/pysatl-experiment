from stattest.core.store import FastJsonStoreService, write_json


class CacheResultService(FastJsonStoreService):

    def get_with_prefix(self, keys: [str]) -> {}:
        """
        Get JSON value by prefix chain in 'keys' param.

        :param keys: keys chain prefix param
        """

        key_prefix = self._create_key(keys)
        result = {}
        for key in self.cache:
            if key.startswith(key_prefix):
                result[key] = self.get(key)
        return result

    def get_level_prefixes(self, keys: [str], level: int) -> set:
        """
        Get JSON value by prefix chain in 'keys' param.

        :param keys:
        :param level:
        """

        key_prefix = self._create_key(keys)
        result = []
        for key in self.cache:
            split = key.split(self.separator)
            if len(split) > level and key.startswith(key_prefix):
                result.append(split[level])
        return set(result)


class ThreadSafeCacheResultService(CacheResultService):
    def __init__(self, filename='result.json', separator=':', cache=None, lock=None):
        super().__init__(filename=filename, separator=separator)
        self.filename = filename
        self.separator = separator
        self.cache = cache
        self.lock = lock

    def flush(self):
        """
        Flush data to persisted store.
        """

        with self.lock:
            cache_dict = dict(self.cache)
            write_json(self.filename, cache_dict)

    def put(self, key: str, value):
        """
        Put object to cache.

        :param key: cache key
        :param value: cache value
        """
        with self.lock:
            self.cache[key] = value

    def put_with_level(self, keys: [str], value):
        """
        Put JSON value by keys chain in 'keys' param.

        :param value: value to put
        :param keys: keys chain param
        """

        key = self._create_key(keys)
        with self.lock:
            self.cache[key] = value

    def set_filename(self, filename: str):
        """
        Sets filename field.

        Parameters
        ----------
        filename : str
            Filename.
        """

        self.filename = filename

    def set_separator(self, separator: str):
        """
        Sets filename field.

        Parameters
        ----------
        separator : str
            Filename.
        """

        self.separator = separator
