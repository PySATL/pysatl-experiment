from abc import ABC, abstractmethod

from stattest.parsable import Parsable


class AbstractHypothesis(Parsable, ABC):
    @abstractmethod
    def generate(self, size, **kwargs):
        raise NotImplementedError("Method is not implemented")
