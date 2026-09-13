# UPD Commander integration

`math_sim` adopts the UPD Commander Base Design incrementally for the Python parent application.

## Layers

- `ui/`: Tkinter-facing commanders, messengers, and UI processing.
- `process/`: simulation/application commanders, messengers, and process processing.
- `data/`: reserved for persistence, saved presets, imported datasets, and other data-layer responsibilities.
- `contracts/`: DTO/message contracts shared across layer boundaries.

## Dependency rule

The intended request path is:

```text
UI Processing
  -> UI Commander
  -> UI Messenger
  -> Process Messenger
  -> Process Commander
  -> Process Processing
```

UI code must not call native engines directly once a feature has been migrated. Native C++ engine wrappers belong behind Process Processing.

## Migration policy

Migration is incremental to avoid destabilizing the existing application. Path Finding is the first migrated feature and serves as the reference implementation. Existing simulations can be moved feature-by-feature while retaining compatibility wrappers in `math_sim.ui`.

Future persistence features should use the full `UI <-> Process <-> Data` route rather than importing Data-layer modules from UI code.
