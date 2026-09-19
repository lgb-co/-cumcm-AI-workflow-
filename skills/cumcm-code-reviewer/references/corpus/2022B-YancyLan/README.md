# -2022CUMCM-B-Mathematics-Modelling
Team: Wenjie Lan; Zhixi Li, Xudong Yin
A full project for Question B in 2022 ChinaUndergraduate Mathematical Contest in Modelling which won 2nd National Price

**What it does.** Estimates UAV position using **passive observations** (RSSI, Angle-of-Arrival, TDoA) only.

**How it works.**
- **Measurement models → likelihood/posterior** with geometric constraints (feasible area/speed/turn limits).
- **Robust MLE** (Huber/RANSAC) with **Gauss–Newton** refinement; covariance-based **uncertainty quantification**.
- Metrics: **RMSE/MAE**, convergence curves.
