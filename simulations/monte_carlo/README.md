# Monte Carlo simulation

## Pi estimation

The first simulation estimates pi using uniformly distributed random points.

1. Sample points `(x, y)` uniformly from the square `[-1, 1] x [-1, 1]`.
2. Count points satisfying `x^2 + y^2 <= 1`.
3. The area ratio approaches `pi / 4`, so:

```text
pi ~= 4 * inside_circle / samples
```

The initial implementation lives in `python/math_sim/simulations/monte_carlo.py` and uses NumPy. A future C++ engine can implement the same model for performance comparisons.
