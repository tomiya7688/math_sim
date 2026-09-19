# Physics backend architecture

Issue #7 introduces a backend-neutral physics boundary for educational simulations.

## Common API

`cpp/include/math_sim/physics.hpp` defines `PhysicsWorld`, body creation/removal,
gravity, stepping, pause/reset, and state queries. Demo code should depend on this
contract rather than directly on Box2D, Jolt Physics, or another engine.

The repository currently ships a dependency-free `EulerPhysicsWorld`. It is a
small point-mass translation backend for demonstrations that do not need
collision detection. It uses semi-implicit Euler integration and deliberately
does not pretend to be a rigid-body collision engine.

## External engine policy

External engines are optional adapters. Before an adapter becomes a bundled
runtime dependency, all of the following must be recorded:

- exact version or commit
- upstream repository
- license and copyright
- transitive runtime dependencies
- required license/notice files
- static/dynamic linking choice
- files copied into the distribution

Candidates checked for this architecture include Box2D (2D) and Jolt Physics
(3D). Both upstream projects currently state MIT licensing. This repository
does not bundle either candidate yet; their metadata is recorded in
`third_party/physics_engines.json`.

A future adapter should implement `PhysicsWorld` and keep engine-specific
types out of demo/domain headers.
