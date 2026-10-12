"""Validate anatomical labels and compute physical template volumes."""
from pathlib import Path
import numpy as np
import pandas as pd
import nibabel as nib
from .common import write_json, sha256
ATLAS_NAME = "nextbrain_wholebrain_MNI152_1mm.nii.gz"
LUT_NAME = "nextbrain_wholebrain_MNI152_1mm_lut.txt"
OFFSET = 10000

def hemisphere(label):
    label = int(label)
    if label == 0:
        return "background", 0
    if 0 < label < OFFSET:
        return "left", label
    if OFFSET < label < 2 * OFFSET:
        return "right", label - OFFSET
    return "unexpected", label

def read_lut(path):
    rows, seen = [], set()
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        f = line.split()
        if len(f) < 6:
            raise ValueError(f"Malformed LUT line {line_no}")
        label, name = int(f[0]), " ".join(f[1:-4])
        rgba = [int(c) for c in f[-4:]]
        if label in seen or not all(0 <= c <= 255 for c in rgba):
            raise ValueError(f"Duplicate label or invalid colour on LUT line {line_no}")
        seen.add(label)
        side, base = hemisphere(label)
        prefix_ok = label == 0 or name.lower().startswith(side + "-")
        region = name.split("-", 1)[1] if prefix_ok and label else name
        rows.append(dict(label_id=label, name=name, region=region,
                         hemisphere=side, base_label_id=base, prefix_matches=prefix_ok,
                         red=rgba[0], green=rgba[1], blue=rgba[2], alpha=rgba[3]))
    if not rows:
        raise ValueError("Empty LUT")
    return pd.DataFrame(rows).sort_values("label_id").reset_index(drop=True)

def load_labels(path):
    image = nib.load(str(path))
    if len(image.shape) != 3 or min(image.shape) < 1:
        raise ValueError("Expected nonempty 3D NIfTI label map")
    if not np.isfinite(image.affine).all() or abs(np.linalg.det(image.affine[:3, :3])) < 1e-9:
        raise ValueError("Invalid or singular affine")
    unit = image.header.get_xyzt_units()[0]
    if unit != "mm":
        raise ValueError(f"Spatial units must be mm, received {unit!r}")
    data = np.asanyarray(image.dataobj)
    if not np.isfinite(data).all() or np.any(data < 0) or not np.equal(data, np.round(data)).all():
        raise ValueError("Labels must be finite nonnegative integers")
    if data.max() > np.iinfo(np.int32).max:
        raise ValueError("Label out of int32 range")
    return image, data.astype(np.int32)

def region_volumes(image, data, lut):
    values, counts = np.unique(data, return_counts=True)
    t = pd.DataFrame({"label_id": values, "voxel_count": counts})
    # Determinant remains correct for sheared affines.
    voxel_mm3 = float(abs(np.linalg.det(image.affine[:3, :3])))
    t["volume_mm3"] = t.voxel_count * voxel_mm3
    t["volume_ml"] = t.volume_mm3 / 1000
    t = t.merge(lut, on="label_id", how="left", validate="one_to_one")
    t["measurement_type"] = "atlas_template_volume"
    return t

def validation(data, lut):
    present, known = set(map(int, np.unique(data))), set(map(int, lut.label_id))
    rows = []
    for label in sorted(present | known):
        side, base = hemisphere(label)
        entry, problems = lut[lut.label_id == label], []
        if label not in known:
            problems.append("missing_lookup")
        if label not in present:
            problems.append("lookup_label_absent")
        if side == "unexpected":
            problems.append("unexpected_label_range")
        if not entry.empty and not bool(entry.iloc[0].prefix_matches):
            problems.append("hemisphere_prefix_mismatch")
        paired = base + OFFSET if side == "left" else base if side == "right" else None
        counterpart = paired in present if paired is not None else True
        if not counterpart:
            problems.append("unpaired_hemisphere")
        rows.append(dict(label_id=label, in_image=label in present, in_lookup=label in known,
                         counterpart_present=counterpart, status=";".join(problems) or "ok"))
    return pd.DataFrame(rows)

def analyze(root):
    root = Path(root)
    source = root / "data/source_atlas"
    image, data = load_labels(source / ATLAS_NAME)
    lut = read_lut(source / LUT_NAME)
    t, report = region_volumes(image, data, lut), validation(data, lut)
    regions = t[t.label_id != 0].copy()
    t.to_csv(root / "results/tables/all_label_volumes.csv", index=False)
    regions.to_csv(root / "results/tables/region_volumes.csv", index=False)
    report.to_csv(root / "results/tables/label_validation_report.csv", index=False)
    regions.volume_ml.describe(percentiles=[.05, .25, .5, .75, .95]).to_csv(root / "results/tables/region_volume_statistics.csv")
    pairs = regions.pivot(index="base_label_id", columns="hemisphere", values="volume_ml")
    pairs["both_present"] = pairs[["left", "right"]].notna().all(axis=1)
    pairs["difference_right_minus_left_ml"] = pairs.right - pairs.left
    pairs["asymmetry_percent"] = 200 * (pairs.right - pairs.left) / (pairs.right + pairs.left)
    pairs.to_csv(root / "results/tables/hemisphere_pairs.csv")
    m = dict(shape=list(image.shape), affine=image.affine.tolist(),
             voxel_spacing_mm=list(map(float, image.header.get_zooms()[:3])),
             orientation=list(nib.aff2axcodes(image.affine)), storage_dtype=str(image.get_data_dtype()),
             spatial_unit=image.header.get_xyzt_units()[0], qform_code=int(image.header["qform_code"]),
             sform_code=int(image.header["sform_code"]),
             voxel_volume_mm3=float(abs(np.linalg.det(image.affine[:3, :3]))),
             nonbackground_regions=len(regions), expected_regions=496, expected_count_passed=len(regions) == 496,
             hemisphere_counts={str(k): int(v) for k, v in regions.hemisphere.value_counts().items()},
             matched_bilateral_pairs=int(pairs.both_present.sum()),
             unpaired_base_labels=list(map(int, pairs.index[~pairs.both_present])),
             nonbackground_volume_ml=float(regions.volume_ml.sum()), validation_issue_rows=int((report.status != "ok").sum()),
             atlas_sha256=sha256(source / ATLAS_NAME), lut_sha256=sha256(source / LUT_NAME),
             meaning="Hard labels. Volumes belong to the MNI template, not individual patients.")
    write_json(root / "results/atlas_metadata.json", m)
    largest = regions.sort_values("volume_ml", ascending=False).head(10)
    summary = f"""# Atlas inspection\n\nHard-label MNI152 template; no subject measurements or voxelwise probabilities.\n\n- Shape: {m['shape']}; orientation: {m['orientation']}.\n- Spacing: {m['voxel_spacing_mm']} mm; voxel volume: {m['voxel_volume_mm3']} mm³.\n- Nonbackground labels: {len(regions)} (expected 496; pass: {m['expected_count_passed']}).\n- Hemisphere counts: {m['hemisphere_counts']}.\n- Matched bilateral pairs: {m['matched_bilateral_pairs']}; unpaired bases: {m['unpaired_base_labels']}.\n- Labelled template volume: {m['nonbackground_volume_ml']:.3f} mL.\n- Validation issue rows: {m['validation_issue_rows']}.\n\nEqual hemisphere counts do not guarantee identical surviving structures.\nAll nonbackground classes are included, including white matter and labelled ventricular spaces.\nInternal ctx-rh fragments do not override the outer prefix and numeric offset.\n\n## Largest template regions\n\n| Region | mL |\n|---|---:|\n"""
    summary += "\n".join(f"| {r['name']} | {r['volume_ml']:.3f} |" for r in largest.to_dict("records"))
    (root / "results/atlas_summary.md").write_text(summary + "\n", encoding="utf-8")
    return image, data, lut, regions, m
