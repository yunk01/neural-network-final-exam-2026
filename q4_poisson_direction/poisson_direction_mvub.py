import csv
import math
import numpy as np


N = 25
OBS_TIME = 20.0
TRUE_S = 73.0
SIGMA_A = 18.0
N_TRIALS = 5000


def rates(s, pref, width):
    return np.exp(-((s - pref) ** 2) / (2.0 * width**2))


def log_likelihood(s, counts, pref, width):
    lam = OBS_TIME * rates(s, pref, width)
    return float(np.sum(counts * np.log(lam + 1.0e-300) - lam))


def estimate_s(counts, pref, width):
    grid = np.linspace(0.0, 180.0, 721)
    vals = np.array([log_likelihood(x, counts, pref, width) for x in grid])
    s = float(grid[int(vals.argmax())])
    for _ in range(12):
        f = rates(s, pref, width)
        dlog = -(s - pref) / width**2
        score = np.sum((counts - OBS_TIME * f) * dlog)
        # Numerical second derivative is robust for this small one-dimensional problem.
        eps = 1.0e-3
        score_p = np.sum((counts - OBS_TIME * rates(s + eps, pref, width)) * (-(s + eps - pref) / width**2))
        score_m = np.sum((counts - OBS_TIME * rates(s - eps, pref, width)) * (-(s - eps - pref) / width**2))
        hess = (score_p - score_m) / (2.0 * eps)
        if abs(hess) < 1.0e-10:
            break
        s = min(180.0, max(0.0, s - score / hess))
    return s


def fisher_information(s, pref, width):
    f = rates(s, pref, width)
    return float(OBS_TIME * np.sum(f * ((s - pref) ** 2) / width**4))


def main():
    pref = np.linspace(0.0, 180.0, N)
    width = np.full(N, SIGMA_A)
    rng = np.random.default_rng(20260701)
    lam = OBS_TIME * rates(TRUE_S, pref, width)
    estimates = np.empty(N_TRIALS)
    squared_errors = np.empty(N_TRIALS)
    for r in range(N_TRIALS):
        counts = rng.poisson(lam)
        estimates[r] = estimate_s(counts, pref, width)
        squared_errors[r] = (estimates[r] - TRUE_S) ** 2

    bias = float(estimates.mean() - TRUE_S)
    var = float(estimates.var(ddof=1))
    mse = float(squared_errors.mean())
    crlb = 1.0 / fisher_information(TRUE_S, pref, width)

    with open("direction_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"N={N}\n")
        f.write(f"obs_time={OBS_TIME:.10f}\n")
        f.write(f"true_s={TRUE_S:.10f}\n")
        f.write(f"sigma_a={SIGMA_A:.10f}\n")
        f.write(f"trials={N_TRIALS}\n")
        f.write(f"bias={bias:.10f}\n")
        f.write(f"variance={var:.10f}\n")
        f.write(f"mse={mse:.10f}\n")
        f.write(f"crlb={crlb:.10f}\n")

    with open("direction_sample_estimates.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["trial", "estimate", "squared_error"])
        for i in range(min(200, N_TRIALS)):
            writer.writerow([i, estimates[i], squared_errors[i]])

    print(f"bias={bias:.6f}, variance={var:.6f}, mse={mse:.6f}, crlb={crlb:.6f}")


if __name__ == "__main__":
    main()
