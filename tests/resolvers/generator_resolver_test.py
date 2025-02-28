from pathlib import Path

import pytest

from stattest.resolvers.generator_resolver import GeneratorResolver


@pytest.mark.parametrize(
    ("generator", "params", "result"),
    [
        ("CauchyRVSGenerator", {"t": 1, "s": 3}, "cauchy_1_3"),
        ("LognormGenerator", {"s": 1, "mu": 3}, "lognorm_1_3"),
        ("BetaRVSGenerator", {"a": 2, "b": 3}, "beta_2_3"),
    ],
)
def test_load_generator_with_params(generator, params, result):
    generator = GeneratorResolver.load_generator(generator, None, params)
    assert generator is not None
    assert result == generator.code()


def test_load_generator_with_default_params():
    default_location = Path(__file__).parent / "config/generators"
    generator = GeneratorResolver.load_generator("GeneratorTest", str(default_location))
    assert generator is not None
    assert "generator_test_1_2" == generator.code()


def test_load_generator_without_default_params():
    default_location = Path(__file__).parent / "config/generators"
    generator = GeneratorResolver.load_generator(
        "GeneratorTestWithoutParams", str(default_location), {"a": 3, "b": 2}
    )
    assert generator is not None
    assert "generator_test_without_3_2" == generator.code()
