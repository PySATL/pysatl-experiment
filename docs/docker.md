# Running experiments in Docker

This image ships a self-contained CLI (`experiment`): code + dependencies, no
local install needed. You type commands in your host terminal, they execute
inside the container — the same pattern as trader terminals (e.g. freqtrade):
host terminal → `docker compose run --rm <service> <subcommand>`.

## Quick start

```bash
docker pull <namespace>/pysatl-experiment:latest
mkdir -p user_data
docker run --rm -v "$PWD/user_data:/app/user_data" \
  <namespace>/pysatl-experiment:latest --help
```

With compose (service already mounts `./user_data`):

```bash
mkdir -p user_data
docker compose run --rm pysatl-experiment --help
```

Replace `<namespace>` with the Docker Hub namespace (personal account or the
PySATL organization) once it is confirmed.

## Full scenario

```bash
docker compose run --rm pysatl-experiment create my-exp
docker compose run --rm pysatl-experiment configure my-exp \
  -cr KS \
  -l 0.05 -l 0.01 \
  -s 100 -s 200 \
  -c 1000 \
  -h normal \
  -expt critical_value \
  -con sqlite:///user_data/pysatl.sqlite
docker compose run --rm pysatl-experiment show my-exp
docker compose run --rm pysatl-experiment build-and-run my-exp
```

Notes:

- Command names use dashes: `build-and-run`, not `build_and_run`.
- `configure --connection` is **required**. Inside the container always pass
  `sqlite:///user_data/<name>.sqlite` so the DB lands in the mounted volume.
- Logs go to stderr by default; add `--log-file user_data/<name>.log` to
  `build-and-run` to keep them. Example configs live in
  `experiment_example/configs/`.

## Where the data lives

Everything is in **one folder**: `./user_data` on the host, mounted at
`/app/user_data` in the container (`docker-compose.yml`).

| Artifact | Path on host |
|---|---|
| Experiment configs | `user_data/.experiments/<name>.json` |
| Reports (PDF) | `user_data/.results/<report>.pdf` |
| SQLite databases | `user_data/*.sqlite` |
| Logs (if `--log-file` used) | `user_data/<name>.log` |

**Data survives `docker rm`.** Nothing valuable is written to the container
layer: configs, reports and the DB sit in the volume. Verify it: run an
experiment, remove the container, run again — the results are still there.

Do not override the workdir (`docker run -w <dir>`): the image and compose
pin `WORKDIR /app`, and the `sqlite:///user_data/...` paths are relative to it.

## Database

Default is SQLite in the volume: `sqlite:///user_data/pysatl.sqlite`.
The legacy code default (`AbstractDbStore`) points there as well.

**Power experiments need critical values first.** The checker reads the
`limit_distributions` table, so before a `power` run either execute a
`critical_value` experiment against the same DB file first, or copy a
populated DB into `user_data/`. Without it the power run fails with
`ConnectionError`.

To use an external database, pass any SQLAlchemy URL via `configure
--connection`, e.g. `postgresql://user:pass@host/db`. No code changes needed.

## Migration from the old default

If you ran the project before and have a database in the repo root, move it
into `user_data/` so the new default (`sqlite:///user_data/...`) picks it up:

```bash
mkdir -p user_data
mv pysatl.sqlite user_data/          # if present
mv training_samples.sqlite user_data/ # if present (generation_only runs)
```

## Tags

| Tag | Meaning |
|---|---|
| `latest` | Last stable release. |
| `edge` | Last `main` commit. May be unstable. |
| `vX.Y.Z` | A specific release. |
| `main-<sha>` | A specific commit (`edge` builds only). |

## Links

- Design notes and diagrams: see the project docs and `pysatl_flow.png`.
- CI deploys the image on push to `main` (`edge`) and on releases (`latest`).
