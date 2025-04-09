from typing import Any

from stattest.persistence.models import IResultStore


class ResultReader:
    def __init__(self, result_store: IResultStore, batch_size=100):
        self.result_store = result_store
        self.batch_size = batch_size
        self.offset = 0
        self.items: list[Any] = []
        self.i = 0

    def __iter__(self):
        return self

    def __next__(self):
        self.i += 1
        if self.i >= len(self.items):
            self.items = self.result_store.get_results(offset=self.offset, limit=self.batch_size)
            self.i = 0
            self.offset += self.batch_size
            if len(self.items) == 0:
                raise StopIteration
        return self.items[self.i]
