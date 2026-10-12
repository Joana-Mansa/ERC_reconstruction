import numpy as np
import pytest
from scipy import sparse
from nextbrain_research.probability import estimate_probabilities, entropy, synthetic_maps, load_source_sparse_probability

def test_empirical_probability_including_background():
    maps = np.array([[[[0,1]]], [[[1,1]]]])
    p = estimate_probabilities(maps, [0,1])
    np.testing.assert_allclose(p.sum(axis=-1),1)
    np.testing.assert_allclose(p[0,0,0],[.5,.5])
    np.testing.assert_allclose(p[0,0,1],[0,1])
    np.testing.assert_allclose(entropy(p), [[[1.,0.]]])

def test_probability_label_coverage():
    with pytest.raises(ValueError, match="cover"):
        estimate_probabilities(np.ones((2,2,2,2)),[0])

@pytest.mark.parametrize("bad", [np.array([.2,.2]),np.array([-.1,1.1]),np.array([np.nan,1])])
def test_invalid_probability_distribution(bad):
    with pytest.raises(ValueError):
        entropy(bad)

def test_synthetic_reproducibility_and_registration():
    n,a,p,t = synthetic_maps(seed=5,subjects=3)
    n2,a2,p2,t2 = synthetic_maps(seed=5,subjects=3)
    np.testing.assert_array_equal(n,n2)
    np.testing.assert_array_equal(a,a2)
    np.testing.assert_array_equal(p,p2)
    assert t == t2
    assert not np.array_equal(n,a)
    assert set(np.unique(a)) == {0,1,2,3}
    assert np.allclose(estimate_probabilities(a,[0,1,2,3]).sum(axis=-1),1)

def test_sparse_source_vector_fixture(tmp_path):
    np.save(tmp_path / "size.npy",[2,2,2])
    sparse.save_npz(tmp_path / "label_001.npz", sparse.coo_matrix(([.3,.7],([1,5],[0,0])),shape=(8,1)))
    a = load_source_sparse_probability(tmp_path,"label_001.npz")
    assert a.shape == (2,2,2)
    assert a.ravel()[1] == pytest.approx(.3)
    assert a.ravel()[5] == pytest.approx(.7)
    with pytest.raises(ValueError,match="memory"):
        load_source_sparse_probability(tmp_path,"label_001.npz",max_voxels=2)
