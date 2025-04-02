from stattest.parsable import Parsable


class AbstractRVSGenerator(Parsable):
    def __init__(self, **kwargs):
        pass

    def code(self):
        return NotImplementedError("Method is not implemented")

    @staticmethod
    def _convert_to_code(items: list):
        return "_".join(str(x) for x in items)

    @staticmethod
    def generate(size):
        raise NotImplementedError("Method is not implemented")
