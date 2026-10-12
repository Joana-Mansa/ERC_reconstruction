"""SYNTHETIC probability atlas and separately gated original sparse-map loader."""
from pathlib import Path
import numpy as np
from scipy.ndimage import shift
from scipy import sparse
import nibabel as nib
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from .common import SEED, savefig, write_json

def estimate_probabilities(maps, labels):
    maps = np.asarray(maps)
    labels = np.asarray(labels)
    if maps.ndim != 4 or maps.shape[0] == 0 or len(np.unique(labels)) != len(labels):
        raise ValueError("Expected N × X × Y × Z maps and unique labels")
    if not np.isin(maps, labels).all():
        raise ValueError("Probability label list does not cover all observed labels")
    return np.stack([(maps == label).mean(axis=0) for label in labels], axis=-1).astype(np.float32)

def entropy(probabilities):
    p = np.asarray(probabilities)
    if not np.isfinite(p).all() or np.any(p < 0) or np.any(p > 1) or not np.allclose(p.sum(axis=-1), 1, atol=1e-6):
        raise ValueError("Invalid probability distribution (include background)")
    return -(p * np.log2(np.maximum(p, np.finfo(np.float32).tiny))).sum(axis=-1)

def synthetic_maps(seed=SEED, subjects=24):
    rng = np.random.default_rng(seed)
    shape = (64, 72, 64)
    xyz = np.indices(shape).astype(float)
    centre = np.array([32, 36, 32])
    brain = (((xyz - centre[:, None, None, None]) / np.array([24, 29, 25])[:, None, None, None]) ** 2).sum(axis=0) < 1
    native, aligned, poor, transforms = [], [], [], []
    for subject in range(subjects):
        a = np.zeros(shape, dtype=np.uint8)
        a[brain] = 3  # stylized whole-brain support
        for label, location in [(1, [23, 31, 24]), (2, [41, 31, 24])]:
            c = np.array(location) + rng.normal(0, .8, 3)
            radii = np.array([4.5, 10, 4]) * rng.uniform(.85, 1.15, 3)
            roi = (((xyz - c[:, None, None, None]) / radii[:, None, None, None]) ** 2).sum(axis=0) < 1
            a[roi & brain] = label
        pose = rng.integers(-3, 4, 3)
        moved = shift(a, pose, order=0, mode="constant", cval=0, prefilter=False)
        restored = shift(moved, -pose, order=0, mode="constant", cval=0, prefilter=False)
        error = rng.integers(-2, 3, 3)
        degraded = shift(moved, -pose + error, order=0, mode="constant", cval=0, prefilter=False)
        if not np.array_equal(restored, a):
            raise ValueError("Synthetic support cropped by translation")
        native.append(moved)
        aligned.append(restored)
        poor.append(degraded)
        transforms.append(dict(subject_id=f"SYN-{subject:03d}", translation_vox=pose.tolist(),
                               inverse_translation_vox=(-pose).tolist(), residual_error_vox=error.tolist()))
    return np.stack(native), np.stack(aligned), np.stack(poor), transforms

def save_nifti(data, affine, path):
    image = nib.Nifti1Image(data, affine)
    image.header.set_xyzt_units("mm")
    nib.save(image, path)

def run_synthetic(root):
    root = Path(root)
    native, aligned, poor, transforms = synthetic_maps()
    labels = np.array([0, 1, 2, 3])
    p = estimate_probabilities(aligned, labels)
    p_poor = estimate_probabilities(poor, labels)
    h, h_poor = entropy(p), entropy(p_poor)
    maximum = labels[p.argmax(axis=-1)].astype(np.uint8)
    affine = np.diag([2., 2., 2., 1.])
    affine[:3, 3] = [-64, -72, -64]
    for name, value in [("SYNTHETIC_native_labels", np.moveaxis(native, 0, -1)),
                        ("SYNTHETIC_aligned_labels", np.moveaxis(aligned, 0, -1)),
                        ("SYNTHETIC_probabilities", p), ("SYNTHETIC_maximum_probability_labels", maximum),
                        ("SYNTHETIC_entropy_bits", h)]:
        save_nifti(value, affine, root / f"data/synthetic/{name}.nii.gz")
    write_json(root / "data/synthetic/SYNTHETIC_transforms.json", dict(seed=SEED, transforms=transforms,
               alignment="Known inverse integer translations (ground-truth alignment, not estimated clinical registration)",
               labels={"0": "background", "1": "stylized left medial temporal ellipsoid", "2": "stylized right medial temporal ellipsoid", "3": "stylized brain support"}))
    support = (p[..., 1:3].sum(axis=-1) > 0) | (p_poor[..., 1:3].sum(axis=-1) > 0)
    stats = dict(seed=SEED, subjects=len(aligned), shape=list(aligned.shape[1:]),
                 normalization_max_error=float(abs(p.sum(axis=-1) - 1).max()),
                 good_mean_entropy_roi_support_bits=float(h[support].mean()),
                 poor_mean_entropy_same_roi_support_bits=float(h_poor[support].mean()),
                 synthetic=True, biological_interpretation="None; shape variation and registration errors were simulated",
                 maximum_probability_tie_rule="first label in [0,1,2,3]; ties are not additional evidence")
    write_json(root / "results/synthetic_probability_summary.json", stats)
    sl = 24
    cmap = ListedColormap(["#111827", "#478db0", "#de8954", "#d8dde4"])
    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    items = [(aligned[0, ..., sl] == 1, "Binary SYNTHETIC left component", "gray", 1),
             (native[0, ..., sl], "SYNTHETIC subject 0, displaced", cmap, 3),
             (aligned[0, ..., sl], "Known inverse alignment", cmap, 3),
             (p[..., sl, 1], "P(SYNTHETIC label 1 | location)", "viridis", 1),
             (maximum[..., sl], "SYNTHETIC maximum-probability labels", cmap, 3),
             (h[..., sl], "SYNTHETIC entropy (bits)", "magma", 2)]
    for ax, (a, title, cm, high) in zip(axes.ravel(), items):
        im = ax.imshow(a.T, origin="lower", cmap=cm, vmin=0, vmax=high, interpolation="nearest", extent=[-65, 63, -73, 71])
        ax.set(title=title, xlabel="Synthetic x (mm; L → R)", ylabel="Synthetic y (mm; P → A)")
        if isinstance(cm, str) and title.startswith(("P(", "SYNTHETIC entropy")):
            fig.colorbar(im, ax=ax, shrink=.8)
    fig.suptitle("SYNTHETIC educational atlas • no real subjects and no NextBrain probability maps")
    fig.tight_layout()
    savefig(fig, root / "results/figures/SYNTHETIC_probability_demo.png")
    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    for j in range(4):
        for row, values in enumerate([native, aligned]):
            axes[row, j].imshow(values[j, ..., sl].T, origin="lower", cmap=cmap, vmin=0, vmax=3, interpolation="nearest")
            axes[row, j].set(title=f"SYNTHETIC {j}: {'native pose' if row == 0 else 'aligned'}", xlabel="Synthetic x (voxels)", ylabel="Synthetic y (voxels)")
    fig.tight_layout()
    savefig(fig, root / "results/figures/SYNTHETIC_multiple_subjects.png")
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    for ax, field, title in zip(axes, [h, h_poor], ["Known correct alignment", "Residual translation errors (±2 voxels)"]):
        im = ax.imshow(field[..., sl].T, origin="lower", cmap="magma", vmin=0, vmax=2, interpolation="nearest")
        ax.set(title=title, xlabel="Synthetic x (voxels)", ylabel="Synthetic y (voxels)")
        fig.colorbar(im, ax=ax, label="Entropy (bits)", shrink=.8)
    fig.suptitle("SYNTHETIC: registration error can inflate spatial uncertainty")
    fig.tight_layout()
    savefig(fig, root / "results/figures/SYNTHETIC_registration_uncertainty.png")
    return stats

def load_source_sparse_probability(directory, filename, max_voxels=50_000_000):
    """Read ONE original label_*.npz using size.npy, matching FreeSurfer's
    COO flattened-row implementation. No label IDs or affine are inferred.
    Caller must supply the official file-to-label mapping and geometry.
    """
    directory = Path(directory)
    if Path(filename).name != filename or not filename.startswith("label_") or not filename.endswith(".npz"):
        raise ValueError("Expected a local label_*.npz filename")
    shape = np.load(directory / "size.npy", allow_pickle=False)
    if shape.shape != (3,) or not np.isfinite(shape).all() or np.any(shape <= 0) or not np.equal(shape, np.round(shape)).all():
        raise ValueError("Invalid size.npy")
    shape = tuple(map(int, shape))
    count = int(np.prod(shape, dtype=np.int64))
    if count > max_voxels:
        raise ValueError("Source map exceeds explicit memory budget")
    source = sparse.load_npz(directory / filename).tocoo()
    if source.shape != (count, 1):
        raise ValueError("Expected COO vector of flattened C-order voxel rows")
    dense = np.asarray(source.toarray(), dtype=np.float32).reshape(shape, order="C")
    if not np.isfinite(dense).all() or np.any(dense < 0) or np.any(dense > 1):
        raise ValueError("Invalid source probability values")
    return dense

def inspect_source_probability(directory, filename, output):
    a = load_source_sparse_probability(directory, filename)
    write_json(output, dict(synthetic=False, source_file=filename, shape=list(a.shape),
               minimum=float(a.min()), maximum=float(a.max()), mean=float(a.mean()),
               spatial_affine="Not inferred; must obtain official atlas geometry before overlays",
               label_mapping="Not inferred from filename; must use official metadata",
               full_normalization_check="Requires all original labels including background; one map is insufficient"))
