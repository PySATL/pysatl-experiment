from abc import ABC, abstractmethod

from stattest.iparsable import IParsable


class AbstractHypothesis(IParsable, ABC):
    @abstractmethod
    def generate(self, size, **kwargs):
        raise NotImplementedError("Method is not implemented")
