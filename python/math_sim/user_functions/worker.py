from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path


def main() -> int:
    try:
        config = json.loads(sys.argv[1])
        request = json.loads(sys.stdin.read())
        namespace = runpy.run_path(str(Path(config["path"]).resolve()))
        function = namespace.get(config.get("entrypoint", "evaluate"))
        if not callable(function):
            raise RuntimeError("configured entrypoint is not callable")
        result = function(request.get("values", []), request.get("context", {}))
        print(json.dumps({"value": result}, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
