"""
Per-pixel agreement between two categorical rasters at different resolutions
and CRSs. Resamples the higher-resolution raster onto the lower-resolution
grid using majority (mode) resampling, then computes:

  - overall accuracy
  - Cohen's kappa
  - per-class producer's / user's accuracy + F1
  - Pontius quantity & allocation disagreement
  - confusion matrix (printed and saved as a figure)
"""

import numpy as np
import rasterio
from pathlib import Path
from rasterio.warp import Resampling, reproject
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
)

ROOT = Path(__file__).resolve().parent
COMPARE_DATA = ROOT.parent / "compare" / "data"
RESULTS_DIR = ROOT / "results"

PY_RASTER_PATH = COMPARE_DATA / "result_python.gtiff"
R_RASTER_PATH = COMPARE_DATA / "result_r.tif"
CONFUSION_MATRIX_PATH = RESULTS_DIR / "confusion_matrix.png"


CLASS_CODES = [1, 2, 3, 4, 5, 6]
CLASS_LABELS = [
    "barley", "corn", "permanent meadows",
    "rapeseed", "temporary meadows", "wheat",
]


def pontius_disagreement(cm: np.ndarray) -> dict:
    """Quantity & allocation disagreement (Pontius & Millones, 2011).

    Total disagreement = 1 - overall_agreement = quantity + allocation.
    """
    cm = cm.astype(float)
    N = cm.sum()
    p = cm / N
    rows = p.sum(axis=1)            # producer marginals (reference = py here)
    cols = p.sum(axis=0)            # user marginals    (comparison = r here)
    diag = np.diag(p)
    agreement = diag.sum()
    quantity = np.abs(rows - cols).sum() / 2.0
    omission = rows - diag          # in py but mislabelled by r
    commission = cols - diag        # in r but mislabelled by py
    # Per Pontius & Millones (2011): per-class a_g = 2·min(om, com),
    # but total allocation = Σ a_g / 2  →  Σ min(om, com).
    allocation = np.minimum(omission, commission).sum()
    return {
        "agreement": agreement,
        "quantity": quantity,
        "allocation": allocation,
        "disagreement_total": 1.0 - agreement,
    }


def align_categorical(src_path_high, src_path_low):
    """Resample the high-res raster onto the low-res grid using mode.

    Returns (high_on_low_grid, low) as flat int16 arrays of equal length,
    with any nodata or out-of-class pixels removed.
    """
    with rasterio.open(src_path_low) as low_src:
        low = low_src.read(1)
        dst_transform = low_src.transform
        dst_crs = low_src.crs
        dst_shape = low.shape

    with rasterio.open(src_path_high) as high_src:
        high_on_low = np.zeros(dst_shape, dtype=np.int16)
        reproject(
            source=rasterio.band(high_src, 1),
            destination=high_on_low,
            src_transform=high_src.transform,
            src_crs=high_src.crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=Resampling.mode,
        )

    low = low.astype(np.int16)
    valid = np.isin(high_on_low, CLASS_CODES) & np.isin(low, CLASS_CODES)
    return high_on_low[valid].ravel(), low[valid].ravel()


def per_class_table(cm: np.ndarray, labels):
    """Producer's accuracy, user's accuracy, F1 per class."""
    cm = cm.astype(float)
    tp = np.diag(cm)
    row_sum = cm.sum(axis=1)        # producer denominator
    col_sum = cm.sum(axis=0)        # user denominator
    with np.errstate(divide="ignore", invalid="ignore"):
        producer = np.where(row_sum > 0, tp / row_sum, np.nan)
        user = np.where(col_sum > 0, tp / col_sum, np.nan)
        f1 = np.where(
            (producer + user) > 0,
            2 * producer * user / (producer + user),
            np.nan,
        )
    rows = []
    for i, lab in enumerate(labels):
        rows.append(
            f"  {lab:<20s} producer={producer[i]:.3f}   "
            f"user={user[i]:.3f}   F1={f1[i]:.3f}   support={int(row_sum[i])}"
        )
    return "\n".join(rows)


if __name__ == "__main__":
    if not PY_RASTER_PATH.is_file():
        raise SystemExit(f"Python raster not found: {PY_RASTER_PATH}")
    if not R_RASTER_PATH.is_file():
        raise SystemExit(f"R raster not found: {R_RASTER_PATH}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    y_py, y_r = align_categorical(str(PY_RASTER_PATH), str(R_RASTER_PATH))
    n = len(y_py)

    acc = accuracy_score(y_py, y_r)
    kappa = cohen_kappa_score(y_py, y_r)
    cm = confusion_matrix(y_py, y_r, labels=CLASS_CODES)
    pontius = pontius_disagreement(cm)

    print(f"valid paired pixels : {n:,}")
    print(f"overall accuracy    : {acc:.4f}")
    print(f"cohen's kappa       : {kappa:.4f}")
    print("")
    print("Pontius decomposition:")
    print(f"  agreement         : {pontius['agreement']:.4f}")
    print(f"  quantity disag.   : {pontius['quantity']:.4f}")
    print(f"  allocation disag. : {pontius['allocation']:.4f}")
    print(f"  total disagreement: {pontius['disagreement_total']:.4f}"
          f"  (check: Q + A = {pontius['quantity'] + pontius['allocation']:.4f})")
    print("")
    print("Per-class (rows = py reference, cols = r comparison):")
    print(per_class_table(cm, CLASS_LABELS))
    print("")
    print("Confusion matrix (rows=py, cols=r):")
    print("            " + "  ".join(f"{lab[:5]:>6s}" for lab in CLASS_LABELS))
    for i, lab in enumerate(CLASS_LABELS):
        print(f"  {lab:<10s}" + "  ".join(f"{cm[i, j]:>6d}" for j in range(len(CLASS_LABELS))))

    # ---- Save a confusion-matrix figure for the paper ----
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    fig, ax = plt.subplots(figsize=(5.2, 4.6), constrained_layout=True)
    im = ax.imshow(cm, cmap="viridis", norm=LogNorm(vmin=max(cm.min(), 1), vmax=cm.max()))
    ax.set_xticks(range(len(CLASS_LABELS)))
    ax.set_yticks(range(len(CLASS_LABELS)))
    ax.set_xticklabels(CLASS_LABELS, rotation=35, ha="right", fontsize=8)
    ax.set_yticklabels(CLASS_LABELS, fontsize=8)
    ax.set_xlabel("R classification", fontsize=9)
    ax.set_ylabel("Python classification", fontsize=9)
    ax.set_title(f"Confusion matrix  (κ={kappa:.3f}, OA={acc:.3f})", fontsize=10)
    # annotate cells
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            v = cm[i, j]
            colour = "white" if v < cm.max() * 0.3 else "black"
            ax.text(j, i, f"{v}", ha="center", va="center", fontsize=7, color=colour)
    fig.colorbar(im, ax=ax, label="pixel count (log scale)", shrink=0.85)
    fig.savefig(CONFUSION_MATRIX_PATH, dpi=200,
                bbox_inches="tight", pad_inches=0.05)
    print(f"\nsaved confusion matrix figure to {CONFUSION_MATRIX_PATH}")