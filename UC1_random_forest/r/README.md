# Use Case 1: Random Forest (openEOcubes)

This workflow runs the pre-built openEO process graph in [`full_pg.json`](full_pg.json) against a local [openEOcubes](https://github.com/PondiB/openEOcubes) backend.

The graph trains a random forest on Sentinel-2 L2A reflectance and writes a classified GeoTIFF via `save_result`.

## Quick start (Docker Compose)

From this directory:

```bash
docker compose up
```

This starts:

- `openeocubes-backend` on host port `8000` (`brianpondi/openeocubes`)
- `uc1-random-forest-runner`, which uses the [openeo](https://open-eo.github.io/openeo-r-client/) R client (`>= 1.4.1`) to submit `full_pg.json` and download results to `./results/`

Default test credentials (same as UC2’s local openeocraft stack):

- **Username:** `brian`
- **Password:** `123456`

Override with environment variables if needed:

```bash
OPENEO_USER=brian OPENEO_PASSWORD=123456 docker compose up
```

## R client (`run_pg.R`)

The R script uses `connect()`, `login()`, `parse_graph()`, `create_job()`, `start_job()`, and `download_results()` from the openeo package.

Local run (with openEOcubes already running on port 8000):

```r
install.packages(c("openeo", "jsonlite"))
setwd("UC1_random_forest/r")
source("run_pg.R")
```

Or from the shell:

```bash
Rscript run_pg.R
```

Defaults: `OPENEO_HOST=http://localhost:8000`, `OPENEO_USER=brian`, `OPENEO_PASSWORD=123456`.

## Python client (`run_pg.py`, optional)

An alternative runner using the [openeo Python client](https://open-eo.github.io/openeo-python-client/) is also provided:

```bash
uv sync
uv run run_pg.py
```

Output is written to `./results/result_openeocubes.gtiff`.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENEO_HOST` | `http://openeocubes-backend:8000` (Compose) | openEO API URL |
| `OPENEO_USER` | `brian` | Basic auth username |
| `OPENEO_PASSWORD` | `123456` | Basic auth password |
| `PROCESS_GRAPH` | `./full_pg.json` | Path to the flat process graph JSON |
| `OUTPUT_DIR` | `./results` | Directory for downloaded job results |
| `OPENEO_PORT` | `8000` | Host port mapped to the backend (Compose only) |
| `JOB_POLL_SECONDS` | `15` | Poll interval while waiting for the batch job |
| `JOB_MAX_WAIT_SECONDS` | `86400` | Maximum wait time for the batch job |

## Compare with the Python/dask-ml path

After both workflows finish, use [`../compare`](../compare) to plot and compare the openEOcubes result against the openeo-processes-dask-ml output from [`../python`](../python). Copy the R download into `compare/data/result_r.tif` if needed.

## Requirements

- Docker with Compose enabled (for the bundled stack)
- For local R runs: R `>= 4.2` and openeo `>= 1.4.1`
- For local Python runs: [uv](https://docs.astral.sh/uv/)
- Sufficient CPU/RAM for Sentinel-2 download, cube processing, and RF training (jobs can run for a long time)
