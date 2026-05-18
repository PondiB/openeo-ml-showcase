# Comparison of the results

This directory contains python scripts to compare the classification results
from both the openEOcubes and openeo-processes-dask-ml.

Install the python environment using the UV environment manager using `uv sync`,
then run the analysis using `uv run main.py`. Then, the results will appear in
`results` directory.

For simplification, we provide a contianerized docker deployment. To use it,
simply run `docker compose up`, and the resulting analysis will appear in the
`results` directory.
