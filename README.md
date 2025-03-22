# statistic-test

[![Freqtrade CI](https://github.com/PySATL/pysatl-experiment/workflows/PySATL%20CI/badge.svg)](https://github.com/PySATL/pysatl-experiment/actions)
[![Coverage Status](https://coveralls.io/repos/github/PySATL/pysatl-experiment/badge.svg?branch=main)](https://coveralls.io/github/PySATL/pysatl-experiment?branch=main)
[![Documentation](https://readthedocs.org/projects/pysatl-experiment/badge)](https://pysatl-experiment.readthedocs.io)

This is a test framework for goodness-of-fit statistic tests.

## Architecture

Framework consists of 5 modules

1. Core module - provides distributions, cdf, pdf etc.
2. Persistence module - provides different stores to store data.
3. Experiment module - provides pipeline for experiment and default components for pipeline.
4. Expert system module - provides expert system for goodness-of-fit testing.
5. Tests module - provides different goodness-of-fit tests.

### Experiment architecture

![PYSATL architecture](pysatl_flow.png "PYSATL architecture")

## Default components

### Generators

### Storages
***CriticalValueSqLiteStore*** - store critical values and target distributions in SQLite.  
***CriticalValueFileStore*** - store critical values and target distributions in JSON and CSV.  
***RvsSqLiteStore*** - store generated rvs in SQLite. 
***RvsFileStore*** - store generated rvs in CSV.  
***PowerResultSqLiteStore*** - store PowerCalculationWorker result in SQLite

### Workers

PowerCalculationWorker - calculates goodness-of-fit test power

### Report builders

### Weibull distribution

| №  | Test                                           | Status |
|----|------------------------------------------------|--------|
| 1  | Anderson–Darling                               | Done   |
| 2  | Chi square                                     | Done   |
| 3  | Kolmogorov–Smirnov                             | Done   |
| 4  | Lilliefors                                     | Done   |
| 5  | Cramér–von Mises                               | Done   |
| 6  | Min-Toshiyuki                                  | Done   |
| 7  | Smith and Brian                                | Done   |
| 8  | Ozturk and Korukoglu                           | Done   |
| 9  | Tiku-Singh                                     | Done   |
| 10 | Lockhart-O'Reilly-Stephens                     | Done   |
| 11 | Mann-Scheuer-Fertig                            | Done   |
| 12 | Evans, Johnson and Green                       | Done   |
| 13 | Skewness                                       | Done   |
| 14 | Kurtosis                                       | Done   |
| 15 | Statistic based on stabilized probability plot | Done   |
| 16 | Test statistic of Shapiro Wilk                 | Done   |

### Exponential distribution

| Test                 | Second Header |
|----------------------|---------------|
| Ozturk and Korukoglu | Content Cell  |
| Jackson              | Content Cell  |
| Lewis                | Content Cell  |

### Normal distribution

| Test               | Second Header |
|--------------------|---------------|
| Anderson–Darling   | Content Cell  |
| Kolmogorov–Smirnov | Content Cell  |
| Chi square         | Content Cell  |
| skewness           | Content Cell  |
| kurtosis           | Content Cell  |

## Configuration

### Configuration example

### Installation

```bash
git clone https://github.com/PySATL/pysatl-experiment
```

Install dependencies:

```bash
poetry install
```

### Development

Install requirements

```bash
poetry install --with dev
```

### Pre-commit

Install pre-commit hooks:

```shell
poetry run pre-commit install
```

Starting manually:

```shell
poetry run pre-commit run --all-files --color always --verbose --show-diff-on-failure
```
