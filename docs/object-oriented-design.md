# Object-oriented design and architecture rules

The project treats subsystem boundaries as a first-class design constraint.

## Dependency direction

- UI may call application/process/domain abstractions.
- Simulation/domain modules must not import Tkinter UI modules.
- Engine adapters must not import UI modules.
- Registry and search operate on metadata and must not import concrete demos or engines.
- UPD contracts are layer-neutral.
- UPD process code must not import the UPD UI layer.
- Demo-to-demo internal imports should be avoided; shared behavior belongs in a common abstraction.

Mutable state must have an explicit owner. Prefer operations that preserve invariants over
public mutable fields or shared global state. Prefer composition over inheritance unless a
real substitutable is-a relationship exists.

## CI gate

`tools/architecture/check_dependencies.py` parses Python imports with the standard
library AST module and emits GitHub Actions annotations. Violations return a non-zero exit
code and fail CI.

The rules intentionally start with enforceable dependency boundaries rather than trying to
mechanically score all OOP design qualities.

## oop-design-checker

The referenced `oop-design-checker` currently targets C#/Roslyn/MSBuild, while math_sim
currently contains Python and C++ application code. Therefore it is not run against files it
cannot analyze. The repository keeps `oop-design-checker.json` as the future C# gate
configuration. If a C# project is added, CI should invoke a pinned checker release against
that project; project-owned code should not be broadly suppressed.
