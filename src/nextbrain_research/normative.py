"""SYNTHETIC quadratic mean and age-dependent residual variability.

Three disjoint subject sets: training mean, calibration variability, test scores.
This is a cross-sectional teaching model, not a clinically validated reference.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from scipy.stats import norm
import matplotlib.pyplot as plt
from .common import SEED, write_json, savefig

def generate_dataset(seed=SEED, subjects=600):
    rng = np.random.default_rng(seed)
    ages = rng.uniform(20, 90, subjects)
    # Arbitrary simulated scale, slopes and noise; never calibrated to NextBrain.
    specs = [("SYNTHETIC_hippocampal_volume", 7.5, -.023, -.00035, .42),
             ("SYNTHETIC_thalamic_volume", 14., -.035, -.00035, .75),
             ("SYNTHETIC_caudate_volume", 7., -.015, -.00015, .38)]
    records = []
    for region, baseline, slope, curve, sd in specs:
        age_c = ages - 50
        mean = baseline + slope * age_c + curve * age_c ** 2
        sigma = sd * np.exp(.008 * (ages - 20))
        volumes = mean + rng.normal(size=subjects) * sigma
        for i in range(subjects):
            records.append(dict(subject_id=f"SYN-{i:04d}", age=float(ages[i]), region=region,
                                volume_ml=float(volumes[i]), dataset_source="SYNTHETIC educational generator; no real participants",
                                synthetic=True, simulation_true_mean_ml=float(mean[i]), simulation_true_sd_ml=float(sigma[i])))
    return pd.DataFrame(records)

def validate_dataset(data):
    required = {"subject_id", "age", "region", "volume_ml", "dataset_source"}
    if not required.issubset(data.columns) or data[list(required)].isna().any().any():
        raise ValueError("Missing normative data fields")
    if not np.isfinite(data[["age", "volume_ml"]].to_numpy()).all() or (data.age < 0).any() or (data.volume_ml <= 0).any():
        raise ValueError("Invalid age or measured volume")
    if (data.groupby("subject_id").dataset_source.nunique() > 1).any():
        raise ValueError("Subject IDs must be globally unique across source datasets")

def split_subjects(data, seed=SEED):
    validate_dataset(data)
    splitter = GroupShuffleSplit(n_splits=1, test_size=.2, random_state=seed)
    development, test = next(splitter.split(data, groups=data.subject_id))
    d = data.iloc[development]
    splitter = GroupShuffleSplit(n_splits=1, test_size=.25, random_state=seed + 1)
    train_rel, calibration_rel = next(splitter.split(d, groups=d.subject_id))
    return data.iloc[development[train_rel]].copy(), data.iloc[development[calibration_rel]].copy(), data.iloc[test].copy()

def design(ages):
    x = (np.asarray(ages, dtype=float) - 50) / 30
    return np.column_stack([np.ones_like(x), x, x ** 2])

def fit_model(train, calibration):
    if len(train) < 30 or len(calibration) < 30:
        raise ValueError("At least 30 training and 30 calibration rows per region required")
    beta = np.linalg.lstsq(design(train.age), train.volume_ml, rcond=None)[0]
    residual = calibration.volume_ml.to_numpy() - design(calibration.age) @ beta
    edges = np.quantile(calibration.age, np.linspace(0, 1, 7))
    if len(np.unique(edges)) != len(edges):
        raise ValueError("Need a broad age distribution for six calibration bins")
    membership = np.digitize(calibration.age, edges[1:-1])
    bins = []
    for b in range(6):
        selected = membership == b
        if selected.sum() < 5:
            raise ValueError("Too few observations in an age calibration bin")
        sigma = float(np.std(residual[selected], ddof=1))
        if sigma <= 0:
            raise ValueError("Zero residual variability")
        bins.append(dict(age=float(calibration.age[selected].mean()), sd_ml=sigma, n=int(selected.sum())))
    # Log-linear positive SD, fitted only to calibration residuals.
    sigma_beta = np.polyfit([(b["age"] - 50) / 30 for b in bins], np.log([b["sd_ml"] for b in bins]),
                            deg=1, w=np.sqrt([b["n"] - 1 for b in bins]))
    return dict(mean_coefficients=beta.tolist(), log_sd_coefficients=sigma_beta.tolist(), calibration_bins=bins,
                supported_age_range=[float(max(train.age.min(), calibration.age.min())), float(min(train.age.max(), calibration.age.max()))])

def predict(model, ages):
    a = np.asarray(ages, dtype=float)
    mu = design(a) @ np.asarray(model["mean_coefficients"])
    sigma = np.exp(np.polyval(model["log_sd_coefficients"], (a - 50) / 30))
    return mu, sigma

def run_normative(root):
    root = Path(root)
    data = generate_dataset()
    data.to_csv(root / "data/synthetic/SYNTHETIC_age_volumes.csv", index=False)
    train, calibration, test = split_subjects(data)
    ids = {"train": set(train.subject_id), "calibration": set(calibration.subject_id), "test": set(test.subject_id)}
    if any(ids[a] & ids[b] for a, b in [("train", "test"), ("train", "calibration"), ("test", "calibration")]):
        raise ValueError("Subject-level leakage")
    pd.DataFrame([dict(subject_id=i, split=s, dataset_source="SYNTHETIC") for s, values in ids.items() for i in sorted(values)]).to_csv(root / "results/tables/SYNTHETIC_subject_splits.csv", index=False)
    models, scored, trajectories, metrics = {}, [], [], []
    for region in sorted(data.region.unique()):
        tr, cal, te = [s[s.region == region].copy() for s in (train, calibration, test)]
        model = fit_model(tr, cal)
        mu, sigma = predict(model, te.age)
        te["expected_volume_ml"], te["estimated_conditional_sd_ml"] = mu, sigma
        te["z_score"] = (te.volume_ml - mu) / sigma
        low, high = model["supported_age_range"]
        te["inside_supported_age_range"] = te.age.between(low, high)
        # Extrapolation scores are explicitly withheld from reported evaluations.
        te.loc[~te.inside_supported_age_range, ["expected_volume_ml", "estimated_conditional_sd_ml", "z_score"]] = np.nan
        evaluated = te[te.inside_supported_age_range]
        age_grid = np.linspace(low, high, 200)
        grid_mu, grid_sigma = predict(model, age_grid)
        trajectories.append(pd.DataFrame(dict(region=region, age=age_grid, expected_volume_ml=grid_mu,
                    conditional_sd_ml=grid_sigma, lower_95_prediction_ml=grid_mu - norm.ppf(.975) * grid_sigma,
                    upper_95_prediction_ml=grid_mu + norm.ppf(.975) * grid_sigma, synthetic=True)))
        metric = dict(region=region, evaluated_test_rows=len(evaluated), withheld_extrapolation_rows=int((~te.inside_supported_age_range).sum()),
                      rmse_ml=float(np.sqrt(np.mean((evaluated.volume_ml - evaluated.expected_volume_ml) ** 2))),
                      z_mean=float(evaluated.z_score.mean()), z_sd=float(evaluated.z_score.std(ddof=1)),
                      coverage_95=float((abs(evaluated.z_score) <= norm.ppf(.975)).mean()))
        metrics.append(metric)
        models[region] = model
        scored.append(te)
    scores, trajectory = pd.concat(scored), pd.concat(trajectories)
    scores.to_csv(root / "results/tables/SYNTHETIC_test_deviation_scores.csv", index=False)
    scores[scores.inside_supported_age_range].groupby("region").head(5).to_csv(root / "results/tables/SYNTHETIC_example_individuals.csv", index=False)
    trajectory.to_csv(root / "results/tables/SYNTHETIC_age_trajectories.csv", index=False)
    pd.DataFrame(metrics).to_csv(root / "results/tables/SYNTHETIC_normative_test_metrics.csv", index=False)
    supported = scores[scores.inside_supported_age_range].copy()
    supported["age_bin"] = pd.cut(supported.age, [20, 35, 50, 65, 80, 90], include_lowest=True)
    age_qc = supported.groupby(["region", "age_bin"], observed=True).agg(n=("z_score", "size"), z_mean=("z_score", "mean"), z_sd=("z_score", "std"))
    age_qc.to_csv(root / "results/tables/SYNTHETIC_test_age_bin_qc.csv")
    summary = dict(synthetic=True, seed=SEED, participants=data.subject_id.nunique(),
                   split_subjects={k: len(v) for k, v in ids.items()}, models=models, test_metrics=metrics,
                   interval="Approximate conditional individual 95% interval: mean ±1.96 SD. Gaussian assumption. Not a regression mean confidence interval; parameter uncertainty omitted.",
                   clinical_validity="None. Simulated cross-sectional data with arbitrary volume scale and age effects.")
    write_json(root / "results/SYNTHETIC_normative_summary.json", summary)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, region in zip(axes, sorted(models)):
        d, t = data[data.region == region], trajectory[trajectory.region == region]
        ax.scatter(d.age, d.volume_ml, s=6, alpha=.20, color="#51667c", label="SYNTHETIC observations")
        ax.fill_between(t.age, t.lower_95_prediction_ml, t.upper_95_prediction_ml, color="#72b5cd", alpha=.30, label="Approx. 95% individual interval")
        ax.plot(t.age, t.expected_volume_ml, color="#236b88", lw=2, label="Training quadratic mean")
        ax.set(xlabel="Simulated age (years)", ylabel="Simulated volume (mL)", title=region.replace("SYNTHETIC_", "").replace("_", " "))
    axes[0].legend(fontsize=8)
    fig.suptitle("SYNTHETIC age model • variability calibrated on separate subjects • no clinical conclusions")
    fig.tight_layout()
    savefig(fig, root / "results/figures/SYNTHETIC_age_trajectories.png")
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for region in sorted(models):
        d = supported[supported.region == region]
        name = region.replace("SYNTHETIC_", "").replace("_volume", "")
        axes[0].scatter(d.age, d.z_score, s=11, alpha=.55, label=name)
        axes[1].hist(d.z_score, bins=np.linspace(-4, 4, 24), density=True, histtype="step", linewidth=1.5, label=name)
    for bound in [-1.96, 0, 1.96]:
        axes[0].axhline(bound, color="gray", ls="--", lw=.7)
    x = np.linspace(-4, 4, 200)
    axes[1].plot(x, norm.pdf(x), "k--", label="Standard normal reference")
    axes[0].set(xlabel="Simulated age (years)", ylabel="Held-out deviation z", title="SYNTHETIC held-out individual scores")
    axes[1].set(xlabel="Held-out deviation z", ylabel="Density", title="SYNTHETIC standardized deviations")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    savefig(fig, root / "results/figures/SYNTHETIC_deviation_scores.png")
    return summary
