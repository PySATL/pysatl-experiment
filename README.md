# PySATL Experiment

[![PySATL CI](https://github.com/PySATL/pysatl-experiment/actions/workflows/ci.yaml/badge.svg)](https://github.com/PySATL/pysatl-experiment/actions)
[![Coverage Status](https://coveralls.io/repos/github/PySATL/pysatl-experiment/badge.svg?branch=main)](https://coveralls.io/github/PySATL/pysatl-experiment?branch=main)
[![Documentation](https://readthedocs.org/projects/pysatl-experiment/badge)](https://pysatl-experiment.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CLI framework for goodness-of-fit statistical experiments — critical values, power analysis, time complexity, and sample generation.

> **Project status** — active development on branch `feature/docker-compose-new`,
> version 0.3.0.

---

## ✨ Key features

- **CLI**: create, configure, show, and run experiments via `experiment <command>`.
- **Four experiment types**: `critical_value`, `power`, `time_complexity`, `generation_only`.
- **Parallel execution** with buffering and resume of interrupted runs.
- **PDF report generation**, storage backends: SQLite, JSON, CSV.
- **Criteria library**: goodness-of-fit criteria are provided by the external
  `pysatl-criterion` package — see `experiment criteria` and the
  [pysatl-criterion docs](https://pysatl-criterion.readthedocs.io).

---

## 📖 Requirements

| Item | Version |
|------|---------|
| Python | `>=3.10,<3.13` |
| Dependencies | `numpy`, `scipy`, `matplotlib`, `pandas`, `SQLAlchemy`, `click`, `pydantic`, `pysatl-criterion` (TestPyPI), and others — see `pyproject.toml` |
| Build tool | [Poetry](https://python-poetry.org/) (`>=2.0`) |

---

## 🛠 Installation

### Option 1: Install from PyPI (recommended for users)

```bash
pip install pysatl-experiment
```

> The package is published to TestPyPI. Use
> `pip install --index-url https://test.pypi.org/simple/ pysatl-experiment`
> if the PyPI release is not yet available.

### Option 2: Clone and install via Poetry

```bash
git clone https://github.com/PySATL/pysatl-experiment.git
cd pysatl-experiment
poetry install --with dev
```

### Option 3: Editable install (development)

```bash
git clone https://github.com/PySATL/pysatl-experiment.git
cd pysatl-experiment
pip install -e .
```

---

## 🚀 Quickstart

1. **Create** an experiment:

   ```bash
   poetry run experiment create my-exp
   ```

2. **Configure** it (must specify a database connection — SQLite inside the
   mounted `user_data/` volume when using Docker):

   ```bash
   poetry run experiment configure my-exp \
     -cr KS \
     -l 0.05 -l 0.01 \
     -s 100 -s 200 \
     -c 1000 \
     -h normal \
     -expt critical_value \
     -con sqlite:///user_data/pysatl.sqlite
   ```

3. **Show** the experiment configuration:

   ```bash
   poetry run experiment show my-exp
   ```

4. **Run** it:

   ```bash
   poetry run experiment build-and-run my-exp
   ```

All artifacts (configs, results, SQLite DBs, logs) land in `./user_data/` on
the host — see [Where the data lives](#where-the-data-lives).

> Docker is the recommended way to run without installing anything locally:
> see [docs/docker.md](docs/docker.md) for the full Docker quick start,
> image tags, and deployment notes.

---

## 📖 Documentation

- [docs/docker.md](docs/docker.md) — running experiments in Docker
  (quick start, data layout, database, image tags, deployment TODO).
- [docs/index.md](docs/index.md) — project overview (ReadTheDocs).
- [pysatl-criterion docs](https://pysatl-criterion.readthedocs.io) —
  goodness-of-fit criteria library (external dependency).
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to contribute.

---

## 🛠 Development

Install development dependencies:

```bash
poetry install --with dev
```

Run the full test suite:

```bash
pytest
```

Run a single test file:

```bash
pytest tests/test_<file_name>.py
```

Run linting:

```bash
ruff check src/pysatl_experiment tests
```

Check formatting:

```bash
ruff format --check src/pysatl_experiment tests
```

Type checking:

```bash
poetry run mypy src tests
```

Install and run pre-commit hooks:

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

---

## 🗺 Roadmap

- Publish Docker images to Docker Hub (`<dockerhub-username>/pysatl-experiment`).
- Migrate image publish target to `pysatl/pysatl-experiment` after the
  `pysatl` organisation exists on Docker Hub (issue #1).
- Full architecture page for ReadTheDocs (issue #103).
- CLI and configuration reference pages (`docs/cli.md`, `docs/configuration.md`).

---

## License

MIT License — see [LICENSE](LICENSE).
