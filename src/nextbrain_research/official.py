"""Execute the official installed named-argument FreeSurfer tool on CPU.

Never installs software, obtains licenses, or substitutes an unofficial model.
"""
from pathlib import Path
import os
import platform
import shutil
import subprocess
import time
import json
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from nibabel.processing import resample_from_to
from .atlas import load_labels, read_lut, region_volumes
from .visualization import canonical, draw
from .common import write_json, sha256, savefig

COMMAND = "mri_histo_atlas_segment_fireants"

def preflight():
    home = Path(os.environ.get("FREESURFER_HOME", "/nonexistent"))
    license_path = Path(os.environ.get("FS_LICENSE", str(home / "license.txt")))
    atlas = home / "python/packages/ERC_bayesian_segmentation/atlas_simplified"
    blockers = []
    command = shutil.which(COMMAND)
    if not command:
        blockers.append("Official FreeSurfer command not on PATH")
    if not license_path.is_file():
        blockers.append("No license at FS_LICENSE or FREESURFER_HOME/license.txt")
    if not (atlas / "size.npy").is_file() or not list(atlas.glob("label_*.npz")):
        blockers.append("Original atlas_simplified probability files unavailable")
    return dict(operating_system=platform.system(), command_available=bool(command),
                license_file_present=license_path.is_file(), atlas_present=(atlas / "size.npy").is_file(),
                requested_device="cpu", blockers=blockers)

def run_official(input_path, output_path, threads=4):
    state = preflight()
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    write_json(output_path / "preflight.json", state)
    if state["blockers"]:
        raise RuntimeError("; ".join(state["blockers"]))
    image = nib.load(str(input_path))
    if len(image.shape) != 3 or not np.isfinite(image.affine).all():
        raise ValueError("Input must be a valid 3D MRI")
    command = shutil.which(COMMAND)
    help_result = subprocess.run([command, "--help"], text=True, capture_output=True, timeout=120)
    help_text = help_result.stdout + help_result.stderr
    (output_path / "installed_command_help.txt").write_text(help_text, encoding="utf-8")
    if help_result.returncode != 0 or not all(arg in help_text for arg in ["--i", "--o", "--device", "--side", "--mode", "--threads"]):
        raise RuntimeError("Installed syntax not verified as named arguments; inspect saved help before running")
    run_log = dict(device="cpu", threads=threads, input_sha256=sha256(input_path),
                   help_verified=True, hemispheres=[])
    version_file = Path(os.environ["FREESURFER_HOME"]) / "build-stamp.txt"
    run_log["freesurfer_build"] = version_file.read_text().strip() if version_file.exists() else "unavailable"
    for side in ["left", "right"]:
        if (output_path / f"seg.{side}.nii.gz").exists():
            raise FileExistsError("Refusing to overwrite existing official segmentation")
        args = [command, "--i", str(Path(input_path).resolve()), "--o", str(output_path.resolve()),
                "--device", "cpu", "--side", side, "--mode", "invivo", "--threads", str(threads)]
        start = time.monotonic()
        with (output_path / f"execution_{side}.log").open("w", encoding="utf-8") as log:
            result = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, check=False)
        run_log["hemispheres"].append(dict(side=side, arguments=args, runtime_seconds=time.monotonic() - start, returncode=result.returncode))
        write_json(output_path / "run_configuration.json", run_log)
        if result.returncode != 0:
            raise RuntimeError(f"Official {side} run failed; see execution log")
    qc_official(input_path, output_path)
    return run_log

def qc_official(input_path, output_path):
    """Check actual outputs; original hemisphere labels do not use MNI offset."""
    output_path = Path(output_path)
    reference = canonical(nib.load(str(input_path)))
    ref_data = reference.get_fdata(dtype=np.float32)
    lut = read_lut(output_path / "lut.txt")
    reports = []
    for side in ["left", "right"]:
        im, data = load_labels(output_path / f"seg.{side}.nii.gz")
        table = region_volumes(im, data, lut)
        table["hemisphere"] = side
        table["measurement_type"] = "official_MRI_segmentation_volume"
        table.to_csv(output_path / f"recomputed_volumes_{side}.csv", index=False)
        missing = sorted(set(map(int, np.unique(data))) - set(map(int, lut.label_id)))
        # Same MRI frame; only labels are resampled to the original T1 grid.
        resampled = resample_from_to(im, (reference.shape, reference.affine), order=0)
        a = np.asanyarray(resampled.dataobj).astype(int)
        color = np.zeros((max(int(a.max()), int(lut.label_id.max())) + 1, 4))
        for row in lut.to_dict("records"):
            color[row["label_id"]] = [row["red"]/255, row["green"]/255, row["blue"]/255, float(row["label_id"] != 0)]
        rgb = color[a].astype(np.float32)
        if not np.any(a):
            raise ValueError("Empty segmentation after nearest-neighbour resampling")
        center = np.median(np.argwhere(a > 0), axis=0).astype(int)
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        for ax, axis, view in zip(axes, [2, 1, 0], ["Axial", "Coronal", "Sagittal"]):
            draw(ax, rgb, reference, axis, center[axis], f"Official {side}: {view}", reference=ref_data)
        fig.tight_layout()
        savefig(fig, output_path / f"qc_overlay_{side}.png")
        report = dict(side=side, observed_labels=int(len(np.unique(data[data != 0]))), missing_lookup_labels=missing,
                      native_shape=list(im.shape), native_voxel_volume_mm3=float(abs(np.linalg.det(im.affine[:3, :3]))),
                      output_sha256=sha256(output_path / f"seg.{side}.nii.gz"),
                      official_volume_csv_present=(output_path / f"vols.{side}.csv").exists(),
                      interpolation="nearest-neighbour hard labels", manual_qc_required=True)
        reports.append(report)
    write_json(output_path / "quality_control.json", reports)
    (output_path / "QC_REPORT.md").write_text("# Official segmentation QC\n\nValid NIfTI labels and LUT coverage were checked; native-grid volumes recomputed and labels resampled with nearest neighbours for T1 overlays. Inspect the overlays manually, including hippocampal and subcortical boundaries. Numerical checks alone do not establish anatomical accuracy. This is subject volumetry only if the input is an individual MRI; the MNI reference remains template volumetry.\n", encoding="utf-8")
