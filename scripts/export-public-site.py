#!/usr/bin/env python3
"""Export only the public static site into `_site/` for GitHub Pages.

The repo root holds the full pipeline (scripts/, content/, docs/, inbox/,
AGENTS.md, …). GitHub Pages previously published the whole `main` tree, which
leaked build scripts, case JSON, and internal docs.

Usage:
    python scripts/build-pages.py
    python scripts/validate-cases.py
    python scripts/export-public-site.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"

# Exact root files that visitors need.
ROOT_FILES = (
    ".nojekyll",
    "404.html",
    "CNAME",
    "case.html",
    "index.html",
    "robots.txt",
    "sitemap.xml",
    "tips.html",
)

# Directories copied as-is (runtime static assets / generated pages).
PUBLIC_DIRS = (
    "assets",
    "cases",
    "css",
    "js",
    "tips",
)

# Anything else at repo root must NOT appear under `_site/`.
FORBIDDEN_NAMES = frozenset(
    {
        ".cursor",
        ".ecc",
        ".env",
        ".git",
        ".github",
        ".gitignore",
        "AGENTS.md",
        "NEW_CHAT_PLAYBOOK.md",
        "STATUS.md",
        "WORKFLOW.md",
        "_headers",
        "content",
        "docs",
        "inbox",
        "partials",
        "requirements.txt",
        "scripts",
    }
)


def die(message: str) -> None:
    print(f"export-public-site: {message}", file=sys.stderr)
    raise SystemExit(1)


def reset_out() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)


def copy_root_files() -> None:
    for name in ROOT_FILES:
        src = ROOT / name
        if not src.is_file():
            die(f"required public file missing: {name}")
        shutil.copy2(src, OUT / name)


def copy_public_dirs() -> None:
    for name in PUBLIC_DIRS:
        src = ROOT / name
        if not src.is_dir():
            die(f"required public directory missing: {name}/")
        shutil.copytree(
            src,
            OUT / name,
            ignore=shutil.ignore_patterns(
                ".DS_Store",
                "Thumbs.db",
                "desktop.ini",
                "__pycache__",
                "*.pyc",
                "*.md",
                "*.py",
                "*.json",
            ),
        )


def assert_clean() -> None:
    problems: list[str] = []
    for path in OUT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(OUT)
        top = rel.parts[0]
        if top in FORBIDDEN_NAMES:
            problems.append(rel.as_posix())
        elif path.suffix.lower() in {".py", ".md", ".json"}:
            # Public site is HTML/CSS/JS + media only — no pipeline sources.
            problems.append(rel.as_posix())

    if problems:
        die("forbidden paths in _site:\n  " + "\n  ".join(sorted(problems)))

    top_names = {p.name for p in OUT.iterdir()}
    allowed_top = set(ROOT_FILES) | set(PUBLIC_DIRS)
    extra = sorted(top_names - allowed_top)
    if extra:
        die(f"unexpected top-level entries in _site: {', '.join(extra)}")


def main() -> None:
    reset_out()
    copy_root_files()
    copy_public_dirs()
    assert_clean()
    file_count = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"export-public-site: wrote {file_count} files -> {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
