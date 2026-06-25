import csv
import math
import numpy as np


V_TH = 1.0
V_RESET = 0.0
TAU_REF = 0.005
TAU_SYN = 0.02
G_L = 50.0
G_SYN = 1.0
DT = 1.0e-4
T_MAX = 0.4

TARGET_MEAN = 0.060
TARGET_VAR = 2.0e-4


def simulate_isi(mu, sigma, n_trials=2500, seed=0):
    rng = np.random.default_rng(seed)
    if sigma > 0:
        current = rng.normal(mu, sigma / math.sqrt(2.0 * TAU_SYN), size=n_trials)
    else:
        current = np.full(n_trials, mu, dtype=float)

    voltage = np.full(n_trials, V_RESET, dtype=float)
    alive = np.ones(n_trials, dtype=bool)
    isi = np.full(n_trials, np.nan)
    sqrt_dt = math.sqrt(DT)

    for k in range(1, int(T_MAX / DT) + 1):
        idx = alive
        if not idx.any():
            break
        current[idx] += (-(current[idx] - mu) / TAU_SYN) * DT
        if sigma > 0:
            current[idx] += (sigma / TAU_SYN) * sqrt_dt * rng.standard_normal(idx.sum())
        voltage[idx] += (-G_L * voltage[idx] + G_SYN * current[idx]) * DT
        hit = idx & (voltage >= V_TH)
        if hit.any():
            isi[hit] = k * DT + TAU_REF
            alive[hit] = False

    isi = isi[~np.isnan(isi)]
    return {
        "n": int(isi.size),
        "hit_fraction": float(isi.size / n_trials),
        "mean": float(isi.mean()),
        "variance": float(isi.var(ddof=1)),
    }


def tune_mu_for_mean(sigma, target_mean=TARGET_MEAN):
    lo, hi = 51.0, 75.0
    for _ in range(20):
        mid = 0.5 * (lo + hi)
        stat = simulate_isi(mid, sigma, n_trials=900, seed=123)
        if stat["mean"] > target_mean:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main():
    deterministic_mu = G_L * V_TH / (
        G_SYN * (1.0 - math.exp(-G_L * (TARGET_MEAN - TAU_REF)))
    )
    grid_rows = []
    best = None
    for sigma in np.linspace(0.1, 0.7, 13):
        mu = tune_mu_for_mean(float(sigma))
        stat = simulate_isi(mu, float(sigma), n_trials=2500, seed=456)
        score = (
            abs(stat["mean"] - TARGET_MEAN) / TARGET_MEAN
            + abs(stat["variance"] - TARGET_VAR) / TARGET_VAR
        )
        row = {
            "sigma": float(sigma),
            "mu": mu,
            "mean": stat["mean"],
            "variance": stat["variance"],
            "hit_fraction": stat["hit_fraction"],
            "score": float(score),
        }
        grid_rows.append(row)
        if best is None or score < best["score"]:
            best = row

    with open("lif_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["sigma", "mu", "mean", "variance", "hit_fraction", "score"]
        )
        writer.writeheader()
        writer.writerows(grid_rows)

    with open("lif_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"deterministic_mu={deterministic_mu:.10f}\n")
        f.write(f"target_mean={TARGET_MEAN:.10f}\n")
        f.write(f"target_variance={TARGET_VAR:.10f}\n")
        for key in ["sigma", "mu", "mean", "variance", "hit_fraction", "score"]:
            f.write(f"best_{key}={best[key]:.10f}\n")

    print("Best calibrated parameters:")
    for key in ["sigma", "mu", "mean", "variance", "hit_fraction", "score"]:
        print(f"{key}: {best[key]:.10f}")


if __name__ == "__main__":
    main()
