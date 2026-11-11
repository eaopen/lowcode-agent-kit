"""Install existing platform Skills into a chosen Agent directory.

A generic installer for any project or user; no project-specific extension.
No credentials are read, no existing Skill is overwritten, and updates follow
the pinned source checkout only when the recipient explicitly runs the tool.
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

SKILL_DIRS = {
    "extn": "lowcode-extn",
    "eap-obpm": "lowcode-eap-obpm",
    "cloudfile": "lowcode-cloudfile",
}


def install(
    source_root: Path,
    destination_root: Path,
    names: list[str],
    *,
    method: str = "link",
    dry_run: bool = False,
) -> list[tuple[str, str]]:
    """Return (skill, outcome); reject collisions instead of overwriting."""
    if method not in {"link", "copy"}:
        raise ValueError("method must be link or copy")
    if not names:
        names = ["extn"]
    source_root = source_root.resolve()
    destination_root = destination_root.expanduser().resolve()

    # Check the entire request before making changes to avoid partial install.
    operations: list[tuple[str, Path, Path, str]] = []
    for name in names:
        if name not in SKILL_DIRS:
            raise ValueError("unknown Skill: " + name)
        source = source_root / "skills" / name
        if not (source / "SKILL.md").is_file():
            raise FileNotFoundError("Skill source not found: " + str(source))
        target = destination_root / SKILL_DIRS[name]
        if target.is_symlink() and target.resolve() == source:
            outcome = "already-linked"
        elif target.exists() or target.is_symlink():
            raise FileExistsError(f"refusing to overwrite an existing Skill: {target}")
        elif source == target:
            outcome = "already-source"
        else:
            outcome = "would-" + method if dry_run else method
        operations.append((name, source, target, outcome))

    if not dry_run:
        for _name, source, target, outcome in operations:
            if outcome == "link":
                destination_root.mkdir(parents=True, exist_ok=True)
                os.symlink(source, target, target_is_directory=True)
            elif outcome == "copy":
                destination_root.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, target)
    return [(name, outcome) for name, _source, _target, outcome in operations]


def main() -> None:
    parser = argparse.ArgumentParser(description="Install generic lowcode Skills without overwriting other installations")
    parser.add_argument("--target", type=Path, required=True, help="User-chosen Agent Skills directory")
    parser.add_argument("--skill", choices=tuple(SKILL_DIRS), action="append", default=[], help="Specific platform Skill (repeatable); defaults to EXTN")
    parser.add_argument("--method", choices=("link", "copy"), default="link", help="link tracks source checkout; copy for Windows without symlink permissions")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing")
    args = parser.parse_args()
    source_root = Path(__file__).resolve().parents[2]
    for name, outcome in install(source_root, args.target, args.skill, method=args.method, dry_run=args.dry_run):
        print(f"{name}: {outcome}")


if __name__ == "__main__":
    main()
