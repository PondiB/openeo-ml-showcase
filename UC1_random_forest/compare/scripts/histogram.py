import rasterio
from matplotlib import pyplot as plt
import numpy as np

import constants


def _get_relative_histogram(data, bins=np.arange(1, 8)):
    """Computes normalized counts for categories 1-6."""
    counts, _ = np.histogram(data, bins=bins)
    return counts / counts.sum()

def histogram():

    py_raster = rasterio.open(constants.PY_RASTER_PATH).read()[0, :, :]
    r_raster = rasterio.open(constants.R_RASTER_PATH).read()[0, :, :]

    py_rel_counts = _get_relative_histogram(py_raster)
    r_rel_counts = _get_relative_histogram(r_raster)

    # Visualization Setup
    categories = np.arange(1, 7)
    labels = [constants.CLASS_NAME_MAPPING[i] for i in categories]
    x = np.arange(len(categories))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots(figsize=(10, 6))

    # Create grouped bars
    rects1 = ax.bar(x - width / 2, py_rel_counts, width, label='openeo-processes-dask-ml',
                    color='skyblue')
    rects2 = ax.bar(x + width / 2, r_rel_counts, width, label='openEOcubes', color='salmon')

    # Formatting the chart
    ax.set_ylabel('Relative Frequency of field class')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    # Optional: Add value labels on top of bars
    ax.bar_label(rects1, padding=3, fmt='%.2f')
    ax.bar_label(rects2, padding=3, fmt='%.2f')

    plt.tight_layout()
    plt.savefig("results/use_case_1_histogram.png")