"""Constants for PySatl experiment system."""

from importlib.resources import files


USERPATH_GENERATORS = "generators"
USERPATH_HYPOTHESIS = "hypothesis"
USER_DATA_DIR = "user_data"
EXPERIMENTS_DIR = ".experiments"
RESULTS_DIR = ".results"
REPORT_TEMPLATE_DIR = str(files("pysatl_experiment") / "resources" / "report_templates")
