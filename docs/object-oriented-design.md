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

## Concrete-base inheritance and review policy

- **Prohibit `concrete A → B → C`.** When B inherits from concrete A, C must not inherit from B, whether B is abstract or concrete.
- **`abstract A → concrete B → C` does not violate this prohibition**, but still requires review for readability, meaningful responsibility boundaries, and substitutability. A further step `concrete B → C → D` is prohibited.
- `concrete A → B` is not prohibited by this policy alone. Preserve stricter existing project rules. Exclude implicit root types such as `Object` and interface inheritance/implementation from this check.
- **Avoid inheriting behavior-bearing classes, including abstract classes with implemented methods, unless inheritance itself is meaningful.** Prefer delegation/composition for simple reuse.
- Use inheritance only for a genuine shared shape/contract already present or reasonably expected to be needed. Reject speculative, purposeless abstraction and any inheritance hierarchy that is hard to read or maintain, even if it passes the mechanical prohibition.
- Exceptions require explicit project architecture documentation of the intentional hierarchy, rationale, and scope. Compiler/analyzer input examples and teaching fixtures are separate from production implementation policy.
- Apply to new/modified project-owned implementation, without mass-changing unrelated legacy code.
