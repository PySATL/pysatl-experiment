# Architecture

## Overview

PySATL Experiment provides a structured 4-step workflow for statistical experiment design, evaluation, and optimization. The system is designed to be modular, allowing researchers to mix and match different experiment types based on their specific needs.

## Experiment Types

The framework supports four distinct experiment types, each serving a specific purpose:

### 1. Critical Value Analysis

**Purpose**: Calculate critical values for statistical tests given a significance level (alpha) and distribution.

**Use case**: Determining the threshold at which a test statistic would lead to rejection of the null hypothesis.

**Configuration**: Uses `normal_critical_values.json` with parameters for distribution, significance level, and degrees of freedom.

### 2. Power Evaluation

**Purpose**: Evaluate the statistical power of tests to detect effects of a given size.

**Use case**: Planning experiments to ensure sufficient sample size for detecting meaningful effects.

**Configuration**: Uses `normal_power.json` with parameters for effect size, sample size, significance level, and power target.

### 3. Time Complexity Measurement

**Purpose**: Measure the performance and time complexity of experiment execution.

**Use case**: Profiling and optimizing experiment pipelines for large-scale studies.

**Configuration**: Uses `normal_time_complexity.json` with parameters for number of iterations, dataset sizes, and measurement parameters.

### 4. Generation Only

**Purpose**: Generate samples or data without performing statistical evaluation.

**Use case**: Rapid prototyping, data generation for testing, or creating baseline datasets.

**Configuration**: Uses `normal_generation_only.json` with parameters for sample generation method and output format.

## Workflow

The standard workflow follows these steps in sequence:

1. **Calculate Critical Values** - Establish the statistical thresholds
2. **Evaluate Power** - Assess the ability to detect effects
3. **Measure Time Complexity** - Profile performance characteristics
4. **Generation Only** - Create samples/data as needed

Each step can be run independently using `poetry run experiment build-and-run <step_number>_<step_name>`.

## Configuration Files

All experiment configurations are stored in `experiment_example/configs/<experiment_type>/` and follow a consistent JSON structure with the following common fields:

- `hypothesis` - The statistical hypothesis being tested
- `distribution` - The assumed data distribution
- `criteria` - Evaluation criteria/tests
- `parameters` - Experiment-specific parameters

## Extension Points

New experiment types can be added by:

1. Creating a new configuration directory under `experiment_example/configs/`
2. Adding a corresponding step in the Quick-Start template
3. Updating the CLI to handle the new step number
4. Adding documentation for the new experiment type
