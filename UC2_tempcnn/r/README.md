# Use Case 2: TempCNN (R)

This use case runs the R openEO TempCNN workflow (training + inference) against an openEO backend using the `brianpondi/openeocraft` Docker image.

## Why it sits on `cube_regularize`

Sentinel‑2 revisit times are **irregular**. `cube_regularize` **fills per-pixel time series** onto a fixed grid (`period`) and raster (`resolution`). With the default footprint — about **one degree square**, **full year 2022**, **30 m**, **16‑day spacing** — the backend must read and synchronize a **very large** number of cube cells and time slices. That step is usually **much slower than training** because it is I/O‑ and memory‑heavy, not GPU‑friendly. Progress may look “stuck” while data is fetched and aggregated.

The **Rondonia samples** used for training are built for a **regular 16‑day (`P16D`) timeline over a full seasonal year**. Keep inference aligned: **`cube_regularize`** uses **`P16D`** and **`2022-01-01` … `2022-12-31`** so time series lengths match **sits** expectations. Changing period or shortening the year without updating training data and the model risks mis‑aligned timelines.

Mitigations:

- Give Docker plenty of **CPU and RAM** (see **Docker resources** below); **exit `137`** often means memory pressure during this phase.
- For full Sentinel-2 context, this workflow now loads **all collection bands by default** (including `SCL` where provided by the backend). This is heavier than NDVI-only subsets.

Optional tuning:

- **`UC2_REGULARIZE_PERIOD`** — default **`P16D`** (override only if your pipeline explicitly uses another step).
- **`UC2_GRID_RESOLUTION`** — default **`30 m`** (coarser values cut work but must stay consistent with your training grid if you use them).
- **`UC2_COLLECTION_BANDS`** — optional comma‑separated openEO **`bands`** override for **`load_collection`**. If unset, **all available bands** are loaded (including `SCL` when present).

### “Stuck after band 4” in logs

Per‑band progress usually refers to early **STAC/asset** steps. Because this flow pulls the full band stack by default, logs may appear to advance band-by-band before entering long **`cube_regularize`** work. Multi‑hour **silence** can still mean heavy regularization or I/O, not necessarily an error — check **`docker stats`**, **`docker compose logs openeocraft-backend`**, and Docker Desktop memory.

## Prerequisites

- Docker with Compose enabled

## Docker resources (recommended for speed)

Docker Desktop runs containers in a **Linux VM**. Training and cube work only use CPU/RAM allocated to that VM, so bump limits before long runs (**Settings → Resources**):

- **CPUs:** most cores you can spare (leave one or two for the host).
- **Memory:** TempCNN / `sits` / Torch benefit from **8 GB or more**; **12–16 GB** helps if your machine allows.
- **Apply & restart** Docker after changing limits.

Optional: enable **VirtioFS** file sharing (in Docker Desktop settings, name varies by version) for faster binds into `./results` and `/work`.

If **`openeocraft-backend` (or Compose) exits with code `137`**, the Linux kernel likely sent **SIGKILL** — often **out-of-memory** inside the Docker VM. Raise **Memory** in Docker Desktop Resources, close other heavy apps, and retry.

## Test credentials (local Compose)

The bundled `openeocraft-backend` is configured for local testing with:

- **Username:** `brian`
- **Password:** `123456`

Use other values only if your backend differs.

## Run with one command

From this directory (`UC2_tempcnn/r`):

```bash
OPENEO_USER="brian" OPENEO_PASSWORD="123456" docker compose up --abort-on-container-exit
```

This command starts:

- `openeocraft-backend` on host port `8001` (mapped to container `8000`)
- `uc2-tempcnn-r`, which executes `usecase2.R`, waits until the job reaches a terminal status, then downloads outputs into `./results`.

Default backend URL for the runner is `http://openeocraft-backend:8000`.
Override with `OPENEO_HOST` if needed.

Optional environment variables for the runner:

- `UC2_REGULARIZE_PERIOD` — default **`P16D`** everywhere.
- `UC2_GRID_RESOLUTION` — default **`30`** m everywhere.
- `UC2_COLLECTION_BANDS` — optional comma‑separated bands for **`load_collection`**; unset means all available bands (including `SCL` when available).
- `JOB_POLL_SECONDS` — poll interval when checking job status (default `15`).
- `JOB_MAX_WAIT_SECONDS` — give up after this many seconds (default `86400`, one day).
