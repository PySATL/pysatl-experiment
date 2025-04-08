from stattest.iparsable import IParsable


class AbstractRVSGenerator(IParsable):
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
