SEPARATOR = '_'
CSV_SEPARATOR = ';'
CSV_ENCODING = 'utf-8'


def build_rvs_file_name(generator_code: str, size: int) -> str:
    return generator_code + SEPARATOR + str(size) + SEPARATOR


def parse_rvs_file_name(name: str) -> tuple:
    split = name.split(SEPARATOR)
    size = int(split[-2])
    return SEPARATOR.join(split[:-2]), size


if __name__ == '__main__':
    parse_rvs_file_name('beta_0.5_0.5_30_.csv')
