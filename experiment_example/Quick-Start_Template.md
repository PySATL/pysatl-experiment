# Quick-Start Template: A 3-Step Experimental Workflow

This directory provides a set of template configuration files for the `pysatl-experiment` framework. It is designed to serve as a starting point for conducting a robust, three-step comparison of statistical goodness-of-fit tests.

The goal of this workflow is to help you make a data-driven decision about which statistical test is best suited for your specific hypothesis and potential alternatives.

## The 3-Step Workflow

This template follows a complete research cycle. Each step answers a different question, and they are designed to be run in sequence.

---

### Step 1: Calibration
File: `1_calculate_critical_values.json`

**The Question:** What are the correct decision thresholds for my chosen tests?

**The Purpose:** Before you can use any statistical test, you must establish its baseline critical values. These values depend on your null hypothesis (the distribution you are testing for), the sample sizes, and the desired significance levels (alpha). This step calibrates your "measurement tools."

**The Command:**
```bash
poetry run experiment build-and-run 1_calculate_critical_values
```
---
### Step 2: Evaluation 
File: `2_evaluate_power.json`

**The Question:** How effective are these tests at detecting the specific deviations I care about?

**The Purpose:** This is the core scientific evaluation. You measure the **statistical power** of each test against one or more alternative hypotheses. A test with high power is very good at correctly rejecting the null hypothesis when it is indeed false. This step tells you which test is most effective for your specific problem.

*This experiment requires the critical values generated in Step 1.*

**The Command:**
```bash
poetry run experiment build-and-run 2_evaluate_power
```

---

### Step 3: Performance Analysis
File: `3_measure_time_complexity.json`

**The Question:** What is the computational cost of using each test?

**The Purpose:** This is the practical, engineering evaluation. If two tests show similar power, the faster one may be preferable, especially in data-intensive applications. This experiment measures the execution time of each test, helping you understand the trade-offs between effectiveness and performance.

**The Command:**
```bash
poetry run experiment build-and-run 3_measure_time_complexity
```

---

## How to Adapt This Template for Your Own Research

To use these files for your own experiment, copy this directory and modify the JSON configurations. The key is to ensure your parameters are consistent across the files.
#### 1. Define Your Null Hypothesis

In all three files (`1_...`, `2_...`, `3_...`), change the `hypothesis` object to match the distribution you want to test for.

**Example: Changing from `Normal` to `Weibull`**
```json
  "hypothesis": "normal"
to
  "hypothesis": "weibull"
```

#### 2. Choose the Criteria to Compare

In all three files, update the `criteria` list to include the tests you want to evaluate.

**Example: Comparing `Liliefos` and `Chi-Squared`**
```json
    "criteria": [
      {
        "criterion_code": "LILLIE",
        "parameters": []
      },
      {
        "criterion_code": "CHI2",
        "parameters": []
      }
    ],
```
#### 3. Define the Alternative Hypothesis

In `2_evaluate_power.json`, modify the `alternatives` array. This is the specific deviation you want your tests to be able to detect.

**Example: Checking if tests for `Weibull` can detect an `Exponential` distribution**
```json
"alternatives": [
      {
        "generator_name": "EXPONENTIALGENERATOR",
        "parameters": [
          0.5,
        ]
      }
    ]
```
#### 4. Adjust Experiment Parameters

You can also change `sample_sizes`, `monte_carlo_count`, and `significance_levels` to fit the scope of your research. Just ensure the `sample_sizes` and `significance_levels` are consistent between the `critical_value` and `power` experiments.

By following this structured, three-step approach, you can systematically evaluate and select the best statistical test for any given problem.

---

## How to Run This Example Workflow

The `pysatl-experiment` command-line tool is designed to look for experiment configurations in a dedicated `.experiment` directory at the root of the project.

Therefore, to run these examples, you must first copy the JSON template files into that location.

**1. Copy the configuration files:**

Firstly you need create files
```bash
poerty run experiment create <1_calculate_critical_values>
```

**2. Run the experiments in sequence:**

Once the files are in the `.experiment` directory, you can execute the workflow steps in order. Make sure you are in the project's root directory.
### First, run the calibration step
```
poetry run experiment build-and-run 1_calculate_critical_values
```
### Second, run the power evaluation
```
poetry run experiment build-and-run 2_evaluate_power
```
### Finally, run the performance analysis
```
poetry run experiment build-and-run 3_measure_time_complexity
```
