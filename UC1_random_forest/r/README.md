# Use Case 1: Random Forest (openEOcubes)

This workflow runs the pre-built openEO process graph in [`full_pg.json`](full_pg.json) against a local [openEOcubes](https://github.com/PondiB/openEOcubes) backend using the [openeo Python client](https://open-eo.github.io/openeo-python-client/).

The graph trains a random forest on Sentinel-2 L2A reflectance and writes a classified GeoTIFF via `save_result`.

## Quick start (Docker Compose)

From this directory:

```bash
docker compose up --build
```

This starts:

- `openeocubes-backend` on host port `8000` (`brianpondi/openeocubes`)
- `uc1-random-forest-runner`, which submits `full_pg.json` and downloads the result to `./results/result_openeocubes.gtiff`

Default test credentials (same as UC2’s local openeocraft stack):

- **Username:** `brian`
- **Password:** `123456`

Override with environment variables if needed:

```bash
OPENEO_USER=brian OPENEO_PASSWORD=123456 docker compose up --build
```

## Manual workflow (backend + client)

**1. Start openEOcubes** (one container, port 8000):

```bash
docker run -p 8000:8000 brianpondi/openeocubes
```

**2. Submit the process graph** from this directory (defaults: `brian` / `123456`, `http://localhost:8000`):

```bash
uv sync
uv run run_pg.py
```

The classified GeoTIFF is written to `./results/result_openeocubes.gtiff`.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENEO_HOST` | `http://openeocubes-backend:8000` (Compose) | openEO API URL |
| `OPENEO_USER` | `brian` | Basic auth username |
| `OPENEO_PASSWORD` | `123456` | Basic auth password |
| `PROCESS_GRAPH` | `./full_pg.json` | Path to the flat process graph JSON |
| `OUTPUT_DIR` | `./results` | Directory for the downloaded GeoTIFF |
| `OPENEO_PORT` | `8000` | Host port mapped to the backend (Compose only) |

## Compare with the Python/dask-ml path

After both workflows finish, use [`../compare`](../compare) to plot and compare the openEOcubes result against the openeo-processes-dask-ml output from [`../python`](../python).

## Requirements

- [uv](https://docs.astral.sh/uv/) for local runs (`uv sync`, `uv run`)
- Docker with Compose enabled (for the bundled stack)
- Sufficient CPU/RAM for Sentinel-2 download, cube processing, and RF training (jobs can run for a long time)
