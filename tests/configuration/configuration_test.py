import pytest

from stattest.configuration.configuration_parser import ConfigurationParser
from stattest.experiment import Experiment


@pytest.mark.parametrize(
    "path",
    [
        "../../config_examples/config_example.json",
    ],
)
def test_load_with_params(path):
    config = ConfigurationParser.parse_config(path)
    assert config is not None

    experiment = Experiment(configuration=config)
    assert experiment is not None
