import numpy as np
import geopandas as gpd
import pandas as pd
import rioxarray
import matplotlib.pyplot as plt
import xvec

import constants


# Aggregate raster values by polygon using mode
def _mode_func(values, axis=None, **kwargs):
    """Return most common integer value, ignoring nodata."""
    values = values[~np.isnan(values)]
    if len(values) == 0:
        return np.nan
    vals, counts = np.unique(values.astype(int), return_counts=True)
    return vals[np.argmax(counts)]


def _agg(raster_file_path: str, language: str) -> gpd.GeoDataFrame:
    # --- Load raster as xarray DataArray ---
    raster = rioxarray.open_rasterio(raster_file_path).squeeze()

    # Ensure integer dtype
    raster = raster.astype(np.int8)

    # --- Load polygons from GeoJSON ---
    polygons = gpd.read_file(constants.FIELD_POLYGONS_PATH)

    # Reproject polygons to raster CRS if needed
    if polygons.crs != raster.rio.crs:
        polygons = polygons.to_crs(raster.rio.crs)

    geom_list = polygons.geometry.values

    result = raster.xvec.zonal_stats(
        geom_list,
        x_coords="x",
        y_coords="y",
        stats=_mode_func,
        method="rasterize"
    )
    result = result.astype(np.int8)

    # --- Attach polygon IDs / attributes if desired ---
    polygon_id = f"{language}_polygon_id"
    result = result.assign_coords(**{polygon_id: ("geometry", polygons.ID)})

    class_col_name = f"{language}_class_id"
    result_dataframe = result.xvec.to_geodataframe(name=class_col_name)

    return result_dataframe[["geometry", polygon_id, class_col_name]]


def aggregate_polygons():
    py_result = _agg(constants.PY_RASTER_PATH, language="py")
    r_result = _agg(constants.R_RASTER_PATH, language="r")

    result = pd.concat([
        r_result[["geometry", "r_polygon_id", "r_class_id"]],
        py_result[["py_polygon_id", "py_class_id"]]
    ], axis=1)

    result["polygon_id_matches"] = result["py_polygon_id"] == result["r_polygon_id"]
    result["class_id_matches"] = result["py_class_id"] == result["r_class_id"]

    class_id_match_count = result[["geometry", "class_id_matches"]].groupby(
        "class_id_matches").count()

    class_id_match_count = class_id_match_count.rename(columns={"geometry": "count"})
    class_id_match_count["prortion"] = class_id_match_count["count"] / len(result)

    print(class_id_match_count)

    result.plot(column="class_id_matches", legend=True)
    plt.savefig("results/map.png")

    result.to_file("results/field_compare.json", driver="GeoJSON")

    # optional: compare with validation class ID (tricky!)
