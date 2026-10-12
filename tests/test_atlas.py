from pathlib import Path
import numpy as np
import nibabel as nib
import pytest
from nextbrain_research.atlas import load_labels, read_lut, hemisphere, region_volumes, validation
from nextbrain_research.common import ROOT

def image(data, affine=None):
    im = nib.Nifti1Image(np.asarray(data, dtype=np.float32), np.eye(4) if affine is None else affine)
    im.header.set_xyzt_units("mm")
    return im

def lut_file(tmp_path):
    p = tmp_path / "lut.txt"
    p.write_text("# lookup\n0 Unknown 0 0 0 0\n48 Left-head_of_caudate 145 160 110 0\n10048 Right-head_of_caudate 145 160 110 0\n")
    return p

@pytest.mark.parametrize("label,expected", [(0,("background",0)), (48,("left",48)), (10048,("right",48)),
                                        (10000,("unexpected",10000)), (20000,("unexpected",20000)), (-1,("unexpected",-1))])
def test_hemisphere_convention(label, expected):
    assert hemisphere(label) == expected

def test_physical_volume_anisotropic_and_sheared(tmp_path):
    affine = np.diag([2.,3.,4.,1.])
    affine[0,1] = .7
    data = np.array([0,48,48,10048]).reshape(2,2,1)
    im = image(data, affine)
    volumes = region_volumes(im, data, read_lut(lut_file(tmp_path))).set_index("label_id")
    assert volumes.loc[48, "volume_mm3"] == pytest.approx(48)
    assert volumes.loc[48, "volume_ml"] == pytest.approx(.048)
    assert volumes.volume_mm3.sum() == pytest.approx(96)

@pytest.mark.parametrize("bad", [np.array([[[.5]]]), np.array([[[-1]]]), np.array([[[np.nan]]]), np.zeros((2,2,2,2))])
def test_reject_non_labels(tmp_path, bad):
    path = tmp_path / "bad.nii.gz"
    nib.save(image(bad), path)
    with pytest.raises(ValueError):
        load_labels(path)

def test_reject_unknown_units(tmp_path):
    im = image(np.zeros((2,2,2)))
    im.header.set_xyzt_units("unknown")
    p = tmp_path / "unknown.nii.gz"
    nib.save(im,p)
    with pytest.raises(ValueError, match="units"):
        load_labels(p)

def test_lut_duplicate_detected(tmp_path):
    p = lut_file(tmp_path)
    with p.open("a") as f:
        f.write("48 Left-other 1 2 3 0\n")
    with pytest.raises(ValueError,match="Duplicate"):
        read_lut(p)

def test_missing_lookup_absent_entry_and_unpaired(tmp_path):
    report = validation(np.array([0,48,123]),read_lut(lut_file(tmp_path))).set_index("label_id")
    assert "missing_lookup" in report.loc[123,"status"]
    assert "lookup_label_absent" in report.loc[10048,"status"]
    assert "unpaired_hemisphere" in report.loc[48,"status"]

def test_internal_ctx_rh_does_not_override_left_prefix(tmp_path):
    p = tmp_path / "ctx.txt"
    p.write_text("2016 Left-ctx-rh-parahippocampal 20 220 60 0\n")
    lut = read_lut(p)
    assert lut.iloc[0].hemisphere == "left"
    assert lut.iloc[0].prefix_matches

def test_downloaded_atlas_integrity():
    source = ROOT / "data/source_atlas"
    if not source.exists():
        pytest.skip("Run download first; unit tests remain usable offline")
    im, data = load_labels(source / "nextbrain_wholebrain_MNI152_1mm.nii.gz")
    lut = read_lut(source / "nextbrain_wholebrain_MNI152_1mm_lut.txt")
    report = validation(data, lut)
    assert report.in_lookup.all()
    assert im.shape == data.shape
    assert region_volumes(im,data,lut).voxel_count.sum() == data.size
    # Do not silently enforce a presumed label count on changed source data.
    count = len(np.unique(data[data != 0]))
    if count != 496:
        import warnings
        warnings.warn(f"Atlas count discrepancy: observed {count}, expected 496")
