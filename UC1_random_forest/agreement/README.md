# Agreement metrics

Per-pixel agreement between the UC1 classification rasters from openeo-processes-dask-ml
(`compare/data/result_python.gtiff`) and openEOcubes (`compare/data/result_r.tif`).

## Run

From this directory:

```bash
uv sync
uv run agreement.py
```

Metrics are printed to the terminal. The confusion matrix figure is saved to `results/confusion_matrix.png`.
