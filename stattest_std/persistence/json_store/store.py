import csv
import os

from stattest.persistence import IRvsStore


class JsonStore(IRvsStore):
    __separator = ';'
    __file_separator = '_'
    __path = 'data5'

    def init(self):
        if not os.path.exists(JsonStore.__path):
            os.makedirs(JsonStore.__path)

    def insert_all_rvs(self, generator_code: str, size: int, data: [[float]]):
        file_path = os.path.join(JsonStore.__path, JsonStore.build_rvs_file_name(generator_code, size) + '.csv')
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=JsonStore.__separator, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(data)

    def insert_rvs(self, code: str, size: int, data: [float]):
        pass

    def get_rvs_count(self, code: str, size: int):
        data = self.get_rvs(code, size)
        if data is None:
            return 0
        return len(data)

    def get_rvs(self, code: str, size: int) -> [[float]]:
        pass

    def clear_all(self):
        pass
        #SqlLiteStore.session.query(RVS).delete()

    @staticmethod
    def build_rvs_file_name(generator_code: str, size: int) -> str:
        return generator_code + JsonStore.__file_separator + str(size) + JsonStore.__file_separator
