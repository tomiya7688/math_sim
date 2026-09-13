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
        context = request.get("context", {})
        if "rows" in request:
            values = [function(row, context) for row in request["rows"]]
            print(json.dumps({"values": values}, ensure_ascii=False))
        else:
            result = function(request.get("values", []), context)
            print(json.dumps({"value": result}, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
