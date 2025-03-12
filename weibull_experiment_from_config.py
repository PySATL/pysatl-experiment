from configuration_parser import parse_config
from stattest.experiment import Experiment


if __name__ == "__main__":
    print("Parsing configuration")
    testPath = "config_examples/weibull_experiment.json"

    experiment_configuration = parse_config(testPath)

    if experiment_configuration is not None:
        experiment = Experiment(experiment_configuration)
        print("Starting experiment")

        # Execute experiment
        experiment.execute()
        print("Success")

    print("Ending work")

#  TODO: different methods for different stores?? also, fool check
#  TODO: add big parsing test
#  TODO: update docker_file
