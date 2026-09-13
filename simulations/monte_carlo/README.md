# Monte Carlo simulation

## Pi estimation

The first simulation estimates pi using uniformly distributed random points.

1. Sample points `(x, y)` uniformly from a square.
2. Count points satisfying `x^2 + y^2 <= 1`.
3. The area ratio approaches `pi / 4`, so:

```text
pi ~= 4 * inside_circle / samples
```

## Implementations

- `python/math_sim/simulations/monte_carlo.py`
  - NumPy reference implementation.
  - Useful for rapid experiments, validation, and benchmarks.
- `cpp/engines/monte_carlo_pi/main.cpp`
  - Native C++ calculation engine.
  - Intended to be launched by the Python parent application.
  - Returns one JSON object on standard output.
- `python/math_sim/engines/monte_carlo.py`
  - Python wrapper for launching the C++ engine.
  - Supports both development builds and the PyInstaller one-dir layout.

The NumPy implementation samples from `[-1, 1] x [-1, 1]`. The C++ implementation samples the equivalent quarter-circle problem on `[0, 1] x [0, 1]`; both use the same estimator `4 * inside / samples`.

## C++ engine interface

```text
monte_carlo_pi --samples 1000000 --seed 42
```

Example output:

```json
{"simulation":"monte_carlo_pi","samples":1000000,"inside":785000,"seed":42,"pi_estimate":3.14,"absolute_error":0.001592653589793}
```

Fixing `--seed` makes an experiment reproducible.
