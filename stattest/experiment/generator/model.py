from abc import ABC, abstractmethod


class AbstractRVSGenerator(ABC):

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def code(self):
        return NotImplementedError("Method is not implemented")

    @staticmethod
    def _convert_to_code(items: list):
        return '_'.join(str(x) for x in items)

    @staticmethod
    @abstractmethod
    def generate(size: int):
        pass
