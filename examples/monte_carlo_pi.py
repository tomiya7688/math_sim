from math_sim.simulations import estimate_pi


if __name__ == "__main__":
    result = estimate_pi(samples=1_000_000, seed=42)
    print(f"samples: {result.samples}")
    print(f"inside circle: {result.inside_circle}")
    print(f"estimated pi: {result.estimate:.10f}")
    print(f"absolute error: {result.absolute_error:.10f}")
