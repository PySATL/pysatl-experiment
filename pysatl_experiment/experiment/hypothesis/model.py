from abc import ABC, abstractmethod


class AbstractHypothesis(ABC):
    @abstractmethod
    def generate(self, size, **kwargs):
        raise NotImplementedError("Method is not implemented")
