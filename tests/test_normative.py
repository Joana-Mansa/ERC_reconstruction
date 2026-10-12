import numpy as np
import pandas as pd
import pytest
from nextbrain_research.normative import generate_dataset, split_subjects, fit_model, predict, validate_dataset

def test_deterministic_simulation():
    pd.testing.assert_frame_equal(generate_dataset(seed=4,subjects=20),generate_dataset(seed=4,subjects=20))
    assert generate_dataset(subjects=20).synthetic.all()

def test_repeated_subject_observations_never_cross_splits():
    d = generate_dataset(subjects=100)
    repeated = pd.concat([d,d.assign(age=d.age+1)],ignore_index=True)
    tr,ca,te = split_subjects(repeated)
    sets = [set(t.subject_id) for t in [tr,ca,te]]
    assert not (sets[0]&sets[1] or sets[0]&sets[2] or sets[1]&sets[2])
    assert len(tr)+len(ca)+len(te) == len(repeated)

def test_recovery_of_simulated_mean_and_variability():
    d = generate_dataset(seed=123,subjects=2000)
    tr,ca,te = split_subjects(d,seed=123)
    region = "SYNTHETIC_hippocampal_volume"
    model = fit_model(tr[tr.region==region],ca[ca.region==region])
    test = te[te.region==region]
    mu,sd = predict(model,test.age)
    assert np.sqrt(np.mean((mu-test.simulation_true_mean_ml)**2)) < .10
    z = (test.volume_ml-mu)/sd
    assert abs(z.mean()) < .2
    assert .75 < z.std() < 1.25
    assert np.all(sd>0)
    assert .88 < (abs(z)<=1.96).mean() <= 1

def test_invalid_data_rejected():
    d = generate_dataset(subjects=20)
    d.loc[0,"age"] = np.nan
    with pytest.raises(ValueError):
        validate_dataset(d)
