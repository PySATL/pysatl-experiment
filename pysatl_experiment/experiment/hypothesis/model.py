from abc import ABC, abstractmethod


class AbstractHypothesis(ABC):
    @staticmethod
    @abstractmethod
    def code() -> str:
        """
        Hypothesis unique code.
        """
        pass


class AbstractGofHypothesis(AbstractHypothesis):
    @abstractmethod
    def generate(self, size, **kwargs):
        raise NotImplementedError("Method is not implemented")
