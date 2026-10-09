from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def ensure_parent(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_json(data: Any, path: str | Path) -> None:
    p = ensure_parent(path)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_rows_csv(rows: list[dict], path: str | Path, fields: list[str] | None = None) -> None:
    p = ensure_parent(path)
    if not rows:
        p.write_text("", encoding="utf-8")
        return
    if fields is None:
        fields = sorted({key for row in rows for key in row})
    with p.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
