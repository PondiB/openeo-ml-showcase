import rasterio
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches  # <-- Imported for the discrete legend
import numpy as np

import constants


def plot():
    py_raster = rasterio.open(constants.PY_RASTER_PATH).read()[0, :, :]
    r_raster = rasterio.open(constants.R_RASTER_PATH).read()[0, :, :]

    # 1. Create a strictly discrete colormap with exactly 6 colors
    base_cmap = plt.colormaps['viridis']
    colors = base_cmap(np.linspace(0, 1, 6))
    cmap = mcolors.ListedColormap(colors)

    # Bounds mapping: 1 maps to the 1st color, 2 to the 2nd, etc.
    bounds = np.arange(0.5, 7.5, 1)
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    fig, axes = plt.subplots(2, 1, figsize=(7, 8), constrained_layout=True)

    def show_raster(ax, data, title):
        h, w = data.shape

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

    # 2. Create proxy artists (patches) for the legend matching the map colors
    legend_patches = [
        mpatches.Patch(color=colors[i], label=tick_labels[i])
        for i in range(6)
    ]

    # 3. Add the legend to the figure instead of a colorbar
    fig.legend(
        handles=legend_patches,
        loc="center right",
        bbox_to_anchor=(1.3, 0.5),
        # Pushes the legend to the right side outside the plots
        title="Classes"
    )

    # 4. Added bbox_inches="tight" to prevent the external legend from being clipped
    plt.savefig("results/use_case_1_map.png", bbox_inches="tight")