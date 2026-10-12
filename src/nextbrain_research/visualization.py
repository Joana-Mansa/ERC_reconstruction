from pathlib import Path
import numpy as np
import pandas as pd
import nibabel as nib
from nibabel.processing import resample_from_to
import matplotlib.pyplot as plt
from .common import savefig, write_json

def canonical(image):
    result = nib.as_closest_canonical(image)
    if nib.aff2axcodes(result.affine) != ("R", "A", "S"):
        raise ValueError("Canonical RAS conversion failed")
    if not np.allclose(result.affine[:3, :3], np.diag(np.diag(result.affine[:3, :3]))):
        raise ValueError("Oblique grid needs explicit resampling before slice display")
    return result

def aligned_reference(labels_image, reference_image):
    # Both inputs must be the SAME MNI152 coordinate frame, established by
    # provenance. Resampling handles grids; it is not anatomical registration.
    if reference_image.shape == labels_image.shape and np.allclose(reference_image.affine, labels_image.affine):
        return reference_image, "identical_grid"
    return resample_from_to(reference_image, (labels_image.shape, labels_image.affine), order=1), "T1_linear_resampling_in_shared_MNI152_frame"

def plane(data, axis, index):
    return np.take(data, int(index), axis=axis).T

def extent(image, axis):
    axes = [i for i in range(3) if i != axis]
    edges = []
    for i in axes:
        spacing, start = image.affine[i, i], image.affine[i, 3]
        edges.extend([start - spacing / 2, start + spacing * (image.shape[i] - .5)])
    return edges

def draw(ax, rgb, image, axis, index, title, reference=None, mask=None):
    ext = extent(image, axis)
    if reference is not None:
        a = plane(reference, axis, index)
        ax.imshow(a, origin="lower", extent=ext, cmap="gray", vmin=0, vmax=np.percentile(reference[reference > 0], 99))
    a = np.take(rgb, int(index), axis=axis).transpose(1, 0, 2).copy()
    if mask is not None:
        a[..., 3] *= plane(mask, axis, index)
    if reference is not None:
        a[..., 3] *= .60
    ax.imshow(a, origin="lower", extent=ext, interpolation="nearest")
    coords = ["x: L → R", "y: P → A", "z: I → S"]
    axes = [i for i in range(3) if i != axis]
    world = image.affine[axis, 3] + image.affine[axis, axis] * index
    ax.set(title=f"{title}\n{'xyz'[axis]} = {world:.0f} mm", xlabel=coords[axes[0]] + " (mm)", ylabel=coords[axes[1]] + " (mm)")
    ax.set_facecolor("#101828")

def selected_groups(lut):
    # Transparent name-based selections, not validated complete parent ROIs.
    patterns = {
        "Hippocampal components": r"subiculum|dentate_gyrus|(?:^|_)ca[1-4](?:_|$)|field_ca[1-4]|hippocampus",
        "Amygdala name matches": r"amygdal",
        "Thalamus name matches": r"thalamus|thalamic",
        "Caudate name matches": r"caudate",
        "Cerebellar components": r"cerebell|dentate_\(lateral\)_nucleus|fastigial|interposed|emboliform|globose|floccul|vermis|lobule|culmen|declive|uvula|nodulus|pyramis|tuber",
    }
    return {name: lut[lut.region.str.contains(pattern, case=False, regex=True)] for name, pattern in patterns.items()}

def visualize(root, original, lut, regions):
    root = Path(root)
    figures = root / "results/figures"
    image = canonical(original)
    data = np.asanyarray(image.dataobj).astype(int)
    colors = np.zeros((max(int(data.max()), int(lut.label_id.max())) + 1, 4))
    for r in lut.to_dict("records"):
        # FreeSurfer LUT alpha=0 does not imply invisible anatomy.
        colors[r["label_id"]] = [r["red"] / 255, r["green"] / 255, r["blue"] / 255, float(r["label_id"] != 0)]
    rgb = colors[data].astype(np.float32)
    centres = np.median(np.argwhere(data > 0), axis=0).astype(int)
    views = [(2, "Axial"), (1, "Coronal"), (0, "Sagittal")]
    for axis, name in views:
        # Off-midline sagittal slice shows anatomy rather than mostly background.
        index = centres[axis] + (25 if axis == 0 else 0)
        fig, ax = plt.subplots(figsize=(6, 6))
        draw(ax, rgb, image, axis, index, "NextBrain template: " + name)
        savefig(fig, figures / f"atlas_{name.lower()}.png")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, (axis, name) in zip(axes, views):
        draw(ax, rgb, image, axis, centres[axis] + (25 if axis == 0 else 0), name)
    fig.suptitle("NextBrain MNI152 hard labels • neurological convention (L on left)")
    fig.tight_layout()
    savefig(fig, figures / "atlas_three_view.png")
    ref_path = root / "data/reference/MNI152_T1_1mm.nii.gz"
    ref = None
    if ref_path.exists():
        ref_native = nib.load(ref_path)
        same_native = ref_native.shape == original.shape and np.allclose(ref_native.affine, original.affine)
        aligned, mode = aligned_reference(image, ref_native)
        ref = aligned.get_fdata(dtype=np.float32)
        write_json(root / "results/reference_alignment.json", dict(reference_shape=list(ref_native.shape),
                   reference_affine=ref_native.affine.tolist(), atlas_native_grid_matches=same_native,
                   display_alignment=mode, frame="FSL MNI152 1mm; same template family identified by source atlas README",
                   registration_performed=False, interpolation="linear for intensity, nearest for all hard-label display"))
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        for ax, (axis, name) in zip(axes, views):
            draw(ax, rgb, image, axis, centres[axis] + (25 if axis == 0 else 0), name, reference=ref)
        fig.suptitle("NextBrain labels over FSL MNI152 T1 reference • template, not patient")
        fig.tight_layout()
        savefig(fig, figures / "atlas_T1_overlay.png")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(np.log10(regions.volume_ml), bins=35, color="#356b96", edgecolor="white")
    ax.set(xlabel="log₁₀(template region volume / mL)", ylabel="Region count", title="Template regional volume distribution (496 labels)")
    savefig(fig, figures / "region_volume_histogram.png")
    largest = regions.nlargest(20, "volume_ml").sort_values("volume_ml")
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.barh(largest.name.str.replace("_", " "), largest.volume_ml, color=["#387ca3" if h == "left" else "#cf8654" for h in largest.hemisphere])
    ax.set(xlabel="Template volume (mL)", title="20 largest NextBrain MNI152 labels")
    savefig(fig, figures / "largest_20_regions.png")
    pairs = regions.pivot(index="base_label_id", columns="hemisphere", values="volume_ml").dropna()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(pairs.left, pairs.right, s=14, alpha=.65, color="#387ca3")
    low, high = pairs.min().min() * .7, pairs.max().max() * 1.4
    ax.plot([low, high], [low, high], "--", color="#777777", label="Equal template volume")
    ax.set(xscale="log", yscale="log", xlabel="Left template volume (mL)", ylabel="Right template volume (mL)", title=f"Matched structures only (n={len(pairs)})")
    ax.legend()
    savefig(fig, figures / "left_right_volumes.png")
    matches = []
    fig, axes = plt.subplots(5, 3, figsize=(14, 20))
    for row, (name, entries) in enumerate(selected_groups(lut).items()):
        ids = entries.label_id.to_numpy()
        mask = np.isin(data, ids)
        for record in entries.to_dict("records"):
            matches.append(dict(group=name, label_id=record["label_id"], name=record["name"], selection="LUT name search; illustrative, incomplete parent anatomy"))
        coords = np.argwhere(mask)
        for ax, (axis, view) in zip(axes[row], views):
            if not len(coords):
                ax.text(.5, .5, "No LUT matches", ha="center")
                continue
            # Pick the slice with most selected voxels so thin regions are visible.
            index = int(np.bincount(coords[:, axis]).argmax())
            draw(ax, rgb, image, axis, index, name + " • " + view, reference=ref, mask=mask)
            # Zoom to selected anatomy on THIS slice rather than an empty
            # whole-brain field; world coordinates and orientation are retained.
            slice_points = np.argwhere(np.take(mask, index, axis=axis))
            remaining = [i for i in range(3) if i != axis]
            for dimension, setter in enumerate([ax.set_xlim, ax.set_ylim]):
                i = remaining[dimension]
                low = image.affine[i, 3] + image.affine[i, i] * (slice_points[:, dimension].min() - 8)
                high = image.affine[i, 3] + image.affine[i, i] * (slice_points[:, dimension].max() + 8)
                setter(low, high)
    fig.suptitle("Selected LUT components • name searches are not complete whole-structure masks", y=1)
    fig.tight_layout()
    savefig(fig, figures / "selected_structures.png")
    pd.DataFrame(matches).to_csv(root / "results/tables/selected_structure_labels.csv", index=False)
