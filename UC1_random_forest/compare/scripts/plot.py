import rasterio
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

import constants

def plot():

    py_raster = rasterio.open(constants.PY_RASTER_PATH).read()[0, :, :]
    r_raster = rasterio.open(constants.R_RASTER_PATH).read()[0, :, :]

    # Discrete colormap (1–6)
    cmap = plt.cm.viridis
    bounds = np.arange(0.5, 7.5, 1)
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    fig, axes = plt.subplots(2, 1, figsize=(7, 8), constrained_layout=True)

    def show_raster(ax, data, title):
        h, w = data.shape

        # extent ensures each pixel grid is properly scaled
        im = ax.imshow(
            data,
            cmap=cmap,
            norm=norm,
            origin="upper",
            extent=[0, w, h, 0]
        )

        ax.set_title(title)
        ax.set_xticks([])
        ax.set_yticks([])
        return im

    im1 = show_raster(axes[0], py_raster, "openeo-processes-dask-ml result")
    im2 = show_raster(axes[1], r_raster, "openEOcubes result")

    # Discrete legend labels
    tick_labels = [constants.CLASS_NAME_MAPPING[i] for i in range(1, 7)]

    cbar = fig.colorbar(
        im1,
        ax=axes,
        ticks=np.arange(1, 7),
        fraction=0.03,
        pad=0.04,
        aspect=25
    )

    cbar.set_ticklabels(tick_labels)
    cbar.set_label("Classes")

    plt.savefig("results/use_case_1_map.png")