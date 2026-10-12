import numpy as np
import nibabel as nib
from nextbrain_research.visualization import canonical, aligned_reference

def test_ras_reorientation_preserves_world_position():
    affine = np.diag([-1.,1.,1.,1.])
    affine[0,3] = 4
    data = np.zeros((5,6,7),dtype=np.int16)
    data[1,2,3] = 48
    original = nib.Nifti1Image(data,affine)
    ras = canonical(original)
    point = np.argwhere(np.asanyarray(ras.dataobj)==48)[0]
    np.testing.assert_allclose(nib.affines.apply_affine(affine,[1,2,3]),nib.affines.apply_affine(ras.affine,point))

def test_reference_identical_grid():
    a = nib.Nifti1Image(np.zeros((3,3,3),dtype=np.int16),np.eye(4))
    b,mode = aligned_reference(a,a)
    assert mode == "identical_grid"
    assert b is a
