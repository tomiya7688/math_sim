# GUI architecture decision

## Decision

The current desktop UI implementation remains **Python/Tkinter** for the present
release line.

Tkinter is treated as a replaceable **View adapter**, not as the application or
simulation architecture. This decision does not allow simulation algorithms,
runtime discovery, subprocess management, registry logic, search logic, or
navigation rules to migrate into Tkinter code.

## Distribution contract

End users must not install Python, pip, a compiler, an SDK, or simulation
runtime dependencies.

The Windows distribution is built as a PyInstaller `onedir` package. The parent
application contains its Python runtime and Tk/Tcl runtime, while native
simulation engines are distributed as independent executables under
`engines/`.

The expected runtime shape is:

```text
math_sim/
  math_sim.exe
  _internal/
  engines/
    monte_carlo_pi.exe
    monte_carlo_integral.exe
    random_tree.exe
    perceptron.exe
    mlp.exe
    pathfinding.exe
    pathfinding_advanced.exe
    pathfinding_replanning.exe
    maze.exe
```

Python source files must not be present in the distribution.

## Dependency direction

```text
Tkinter View
    |
    v
Application services / controllers
    |
    v
Engine adapters
    |
    v
EngineProcess
    |
    v
C++ executable subprocess
```

The application entrypoint is the composition root. Views receive their
application services through dependency injection.

Tkinter imports are restricted to the UI layer. UI modules may not import
engine adapters directly, run subprocesses directly, import simulation
implementations directly, or construct application services themselves.

## Why Tkinter remains acceptable

The choice is based on verified build behavior rather than requiring a Python
installation on the target machine:

- Windows self-contained `onedir` packaging passes in CI.
- The packaged parent executable can locate every bundled native engine.
- The packaged parent executable executes the complete native-engine E2E path.
- The packaged application can construct the real Tkinter MainWindow and all
  registered pages in the Windows UI smoke test.
- Native C++ execution is independently checked under ASan/UBSan/LSan on Linux.

Changing to a second desktop framework now would add another build/runtime
surface without removing the native subprocess architecture.

## Re-evaluation criteria

A GUI migration can be reconsidered if a concrete requirement cannot be
satisfied cleanly by the current View layer, for example:

- rendering or animation requirements that are impractical in Tkinter;
- accessibility or high-DPI requirements that cannot be met;
- platform integration that requires another framework;
- measurable UI performance limitations after domain computation remains out
  of process.

Such a migration should replace View adapters while preserving registry,
search, navigation, application controllers, IPC contracts, and C++ engines.

## CI enforcement

The repository continuously verifies:

- normal C++ build and CTest;
- Python syntax and undefined-name checks;
- architecture dependency rules;
- Python unit tests;
- native subprocess E2E;
- ASan/UBSan/LSan native E2E;
- Windows PyInstaller `onedir` build;
- distribution-content validation;
- packaged runtime smoke test;
- packaged Tkinter UI construction smoke test;
- packaged parent-to-engine E2E.

PyInstaller and Ruff versions used by CI are pinned after verified successful
runs.
