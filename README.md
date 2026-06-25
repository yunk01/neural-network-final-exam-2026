# Neural Network Final Exam Code

This repository contains the reproducibility scripts for the selected five
problems in the final exam answer.

## Environment

- Python 3.12.13
- numpy 2.3.5
- Pillow 12.2.0

Install Python dependencies with:

```bash
python3 -m pip install -r requirements.txt
```

## Contents

- `q1_lif/lif_renewal_sim.py`: stochastic LIF inter-spike interval simulation
  and moment calibration.
- `q3_ei_hopf/ei_hopf_sim.py`: E-I rate model parameter scan for the Hopf-like
  transition.
- `q4_poisson_direction/poisson_direction_mvub.py`: Poisson population coding
  direction estimator simulation.
- `q7_maze/maze_solver.py`: maze image parsing and shortest-path/Bellman
  solver. The input image is `q7_maze/maze.jpg`.

Generated CSV/TXT/PNG files are included so the numerical values in the answer
PDF can be checked directly.

## Run

```bash
cd q1_lif && python3 lif_renewal_sim.py
cd ../q3_ei_hopf && python3 ei_hopf_sim.py
cd ../q4_poisson_direction && python3 poisson_direction_mvub.py
cd ../q7_maze && python3 maze_solver.py
```
