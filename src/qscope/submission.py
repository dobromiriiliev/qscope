from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


REQUIRED_FILES = [
    "LICENSE",
    "README.md",
    "ORIGINALITY.md",
    "docs/QOLLAB_PROJECT_PAGE.md",
    "docs/DEMO_SCRIPT.md",
    "configs/mvp.json",
    "notebooks/qollab_demo.ipynb",
]

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|password)\s*[=:]\s*['\"][^'\"]{8,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
]


def validate_repository(root: str | Path) -> list[Check]:
    root = Path(root)
    checks: list[Check] = []

    for rel in REQUIRED_FILES:
        p = root / rel
        checks.append(Check(f"required:{rel}", p.exists(), "present" if p.exists() else "missing"))

    license_path = root / "LICENSE"
    mit = license_path.exists() and "MIT License" in license_path.read_text(encoding="utf-8")
    checks.append(Check("license:MIT", mit, "MIT text found" if mit else "MIT text not found"))

    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").exists() else ""
    for phrase in ("Qiskit", "local", "MIT", "Qollab"):
        ok = phrase.lower() in readme.lower()
        checks.append(Check(f"readme:{phrase}", ok, "mentioned" if ok else "not mentioned"))

    suspicious: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file() or any(part in {".git", ".venv", "__pycache__"} for part in p.parts):
            continue
        if p.suffix.lower() not in {".py", ".md", ".json", ".toml", ".txt", ".yml", ".yaml"}:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            suspicious.append(str(p.relative_to(root)))
    checks.append(
        Check(
            "secrets:basic-scan",
            not suspicious,
            "no obvious secrets" if not suspicious else f"review: {', '.join(suspicious)}",
        )
    )
    return checks


def checks_passed(checks: list[Check]) -> bool:
    return all(c.passed for c in checks)
