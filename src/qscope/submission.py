from __future__ import annotations

from pathlib import Path


REQUIRED = (
    "LICENSE",
    "README.md",
    "ORIGINALITY.md",
    "HACKATHON_LOG.md",
    "docs/QOLLAB_PROJECT_PAGE.md",
    "docs/DEMO_SCRIPT.md",
    "docs/ALGORITHM.md",
    "main.py",
    "notebooks/qollab_demo.ipynb",
    "qollab_demo.py",
    "configs/mvp.json",
)

ATTRIBUTION = "Qollab & IonQ"


def validate_submission(root: str | Path):
    root = Path(root)
    failures = []

    for item in REQUIRED:
        if not (root / item).exists():
            failures.append(f"missing {item}")

    license_path = root / "LICENSE"
    if license_path.exists() and "MIT License" not in license_path.read_text(
        encoding="utf-8"
    ):
        failures.append("LICENSE is not MIT")

    for item in ("README.md", "docs/QOLLAB_PROJECT_PAGE.md"):
        path = root / item
        if path.exists() and ATTRIBUTION not in path.read_text(encoding="utf-8"):
            failures.append(f"missing Qollab/IonQ attribution in {item}")

    originality = root / "ORIGINALITY.md"
    if originality.exists():
        text = originality.read_text(encoding="utf-8").lower()
        if "should be listed" in text or "record meaningful" in text:
            failures.append("ORIGINALITY.md still contains placeholder text")

    log = root / "HACKATHON_LOG.md"
    if log.exists():
        text = log.read_text(encoding="utf-8").lower()
        if "record meaningful" in text:
            failures.append("HACKATHON_LOG.md still contains placeholder text")

    source_root = root / "src"
    if source_root.exists():
        needles = ("ghp_", "api_key=", "token=")

        for path in source_root.rglob("*.py"):
            if path.name == "submission.py":
                continue

            text = path.read_text(encoding="utf-8").lower()
            for needle in needles:
                if needle in text:
                    failures.append(
                        f"possible credential in {path.relative_to(root)}"
                    )

    return failures
