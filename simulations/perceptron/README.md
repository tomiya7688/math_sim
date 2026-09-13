# Perceptron simulation

This simulation demonstrates a single-layer binary perceptron with two inputs.

The reusable Python and C++ APIs accept arbitrary binary training datasets. The parent app provides AND, OR, NAND, and XOR presets so that linearly separable and non-linearly-separable cases can be compared directly.

## Learning rule

For each sample, the perceptron computes:

```text
y = step(w · x + b)
```

and updates parameters when the prediction is wrong:

```text
w <- w + learning_rate * (target - prediction) * x
b <- b + learning_rate * (target - prediction)
```

AND, OR, and NAND are linearly separable and should converge. XOR is not linearly separable, so a single perceptron cannot represent it and normally will not converge.

## Reusable APIs

Python:

```python
from math_sim.simulations import train_perceptron

result = train_perceptron(samples, targets, learning_rate=0.1, epochs=100)
```

C++:

```cpp
#include "math_sim/perceptron.hpp"

auto result = math_sim::perceptron::train(samples, targets, 0.1, 100);
```
