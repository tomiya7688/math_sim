# User-defined functions

`math_sim` has a common numeric-function interface so simulations can accept functions from three sources without coupling calculation code to one language.

## Providers

### 1. Editor expression

Use `provider="expression"` for short formulas entered in the application or loaded from a saved definition.

```python
from math_sim.user_functions import FunctionSpec, create_provider

spec = FunctionSpec(
    name="gaussian",
    provider="expression",
    expression="exp(-x*x)",
)
provider = create_provider(spec)
print(provider.evaluate([2.0]).value)
```

The expression parser accepts arithmetic, `x`/`x0`/`x1`... and a restricted set of math functions. It does not allow imports, attributes, comprehensions, indexing, or Python builtins.

### 2. Python file

A Python user function exports an entrypoint with this shape:

```python
def evaluate(values, context):
    x = values[0]
    return x * x
```

Register it with:

```python
FunctionSpec(
    name="square_py",
    provider="python",
    path="my_functions/square.py",
    entrypoint="evaluate",
)
```

Python files run in a separate process. During development the current Python interpreter is used. In a PyInstaller one-dir distribution, the parent app looks for `engines/math_sim_function_worker(.exe)`.

### 3. C++ executable

A native user function is a standalone executable and uses JSON on stdin/stdout.

Single request:

```json
{"values":[2.0],"context":{}}
```

Single response:

```json
{"value":4.0}
```

Batch request:

```json
{"rows":[[1.0],[2.0],[3.0]],"context":{"simulation":"monte_carlo_integral"}}
```

Batch response:

```json
{"values":[1.0,4.0,9.0]}
```

Register the executable with `provider="cpp"` and `path` pointing at the built program.

## Shared catalog

`FunctionCatalog` can hold all provider types at once:

```python
catalog.add(expression_spec)
catalog.add(python_spec)
catalog.add(cpp_spec)

value = catalog.call("square_py", [3.0]).value
values = catalog.call_many("square_cpp", [[1.0], [2.0], [3.0]])
```

Function definitions can be persisted with `save_spec(...)` / `load_spec(...)`. This is the storage format intended for the future in-app function editor and preset selector.

## Monte Carlo integration

Any provider can be used by the Monte Carlo adapter:

```python
from math_sim.user_functions import monte_carlo_integrate_user_function

result = monte_carlo_integrate_user_function(
    spec,
    lower=0.0,
    upper=1.0,
    samples=100_000,
    seed=42,
)
```

External providers are evaluated in batches so Python/C++ process startup is not repeated for every Monte Carlo sample.

## Security boundary

Expression functions are syntax-restricted. Python and C++ providers are user-supplied executable code and therefore must be treated as trusted local code. Running them in a child process improves crash/error isolation and enables timeouts, but it is **not** a security sandbox.
