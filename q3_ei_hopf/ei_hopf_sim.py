import csv
import numpy as np


M_EE = 2.0
M_EI = 2.0
M_IE = 2.0
M_II = 0.8
TAU_E = 1.0
H_I = 0.5
H_E_BASE = 1.0
DT = 1.0e-3


def rhs(v, tau_i, h_e):
    v_e, v_i = v
    drive_e = max(M_EE * v_e - M_EI * v_i + h_e, 0.0)
    drive_i = max(M_IE * v_e - M_II * v_i + H_I, 0.0)
    return np.array([(-v_e + drive_e) / TAU_E, (-v_i + drive_i) / tau_i])


def simulate(tau_i, h_e=H_E_BASE, total_time=200.0):
    n = int(total_time / DT)
    v = np.empty((n, 2), dtype=float)
    v[0] = np.array([0.10, 0.10])
    for k in range(n - 1):
        v[k + 1] = np.maximum(v[k] + DT * rhs(v[k], tau_i, h_e), 0.0)
    tail = v[int(0.75 * n) :]
    return {
        "mean_e": float(tail[:, 0].mean()),
        "mean_i": float(tail[:, 1].mean()),
        "amp_e": float(tail[:, 0].max() - tail[:, 0].min()),
        "amp_i": float(tail[:, 1].max() - tail[:, 1].min()),
    }


def equilibrium(h_e):
    a = np.array([[1.0 - M_EE, M_EI], [-M_IE, 1.0 + M_II]])
    b = np.array([h_e, H_I])
    return np.linalg.solve(a, b)


def main():
    tau_i_star = TAU_E * (M_II + 1.0) / (M_EE - 1.0)
    det_num = M_EI * M_IE - (M_EE - 1.0) * (M_II + 1.0)
    rows_tau = []
    for tau_i in [1.2, 1.7, 1.8, 1.9, 2.4]:
        stat = simulate(tau_i, H_E_BASE)
        trace = (M_EE - 1.0) / TAU_E - (M_II + 1.0) / tau_i
        det = det_num / (TAU_E * tau_i)
        rows_tau.append({"tau_i": tau_i, "trace": trace, "det": det, **stat})

    rows_he = []
    for h_e in [-2.0, -0.5, 0.0, 1.0, 3.0]:
        eq = equilibrium(h_e)
        stat = simulate(1.2, h_e, total_time=100.0)
        rows_he.append(
            {
                "h_e": h_e,
                "eq_e_active_formula": float(eq[0]),
                "eq_i_active_formula": float(eq[1]),
                **stat,
            }
        )

    with open("tau_i_scan.csv", "w", newline="", encoding="utf-8") as f:
        fields = ["tau_i", "trace", "det", "mean_e", "mean_i", "amp_e", "amp_i"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows_tau)

    with open("h_e_scan.csv", "w", newline="", encoding="utf-8") as f:
        fields = ["h_e", "eq_e_active_formula", "eq_i_active_formula", "mean_e", "mean_i", "amp_e", "amp_i"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows_he)

    with open("ei_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"tau_i_star={tau_i_star:.10f}\n")
        f.write(f"det_numerator={det_num:.10f}\n")

    print(f"tau_i_star={tau_i_star:.6f}, det_numerator={det_num:.6f}")


if __name__ == "__main__":
    main()
