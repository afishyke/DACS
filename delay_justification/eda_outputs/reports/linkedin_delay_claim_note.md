# Why this is the most defensible delay chart

- Selected claim: **One cycle is the strongest defensible minimum from this dataset**.
- The chart uses a causal observation-window test (1 ms to 20 ms), which directly matches delay reasoning in a windowed protection system.
- Separability (AUC) is computed between transient-like classes and sag/swell-like classes using transient-sensitive features identified earlier (derivative energy and high-frequency ratio).
- In this dataset, separability reaches near-maximum only near the end of the cycle (about 19 ms), with best within-cycle value at 20 ms (AUC ~0.700).
- This supports a nonzero delay and makes one full cycle the strongest defensible minimum from this dataset, while still not proving multi-cycle persistence or exact 3/5-cycle delays.
