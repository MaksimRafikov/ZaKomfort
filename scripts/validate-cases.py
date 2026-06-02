#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "js" / "data.js"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_case_ids(data_text: str) -> list[str]:
    # Supports both JSON-style and JS object-style entries.
    pattern = re.compile(r'["\']?id["\']?\s*:\s*["\']([a-z0-9-]+)["\']')
    return pattern.findall(data_text)


def find_asset_paths(data_text: str) -> list[str]:
    # Collect only local asset references used by UI payload.
    pattern = re.compile(
        r'["\'](assets/[A-Za-z0-9_\-./]+\.(?:png|jpg|jpeg|webp|gif|mp4|mov|webm))["\']',
        re.IGNORECASE,
    )
    return pattern.findall(data_text)


def find_inbox_refs(data_text: str) -> list[str]:
    pattern = re.compile(r'["\'](inbox/[A-Za-z0-9_\-./]+)["\']', re.IGNORECASE)
    return pattern.findall(data_text)


def validate() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not DATA_FILE.exists():
        errors.append("Missing required file: js/data.js")
        return errors, warnings

    text = read_text(DATA_FILE)

    ids = find_case_ids(text)
    if not ids:
        errors.append("No case ids found in js/data.js (field `id`).")
    else:
        dupes = sorted({cid for cid in ids if ids.count(cid) > 1})
        if dupes:
            errors.append("Duplicate case ids: " + ", ".join(dupes))

    inbox_refs = sorted(set(find_inbox_refs(text)))
    if inbox_refs:
        errors.append(
            "Found forbidden inbox references in js/data.js: "
            + ", ".join(inbox_refs[:8])
            + (" ..." if len(inbox_refs) > 8 else "")
        )

    asset_paths = find_asset_paths(text)
    if not asset_paths:
        warnings.append("No assets/* media references found in js/data.js.")
    else:
        missing = []
        for p in sorted(set(asset_paths)):
            if not (ROOT / p).exists():
                missing.append(p)
        if missing:
            errors.append(
                "Missing assets referenced by js/data.js: "
                + ", ".join(missing[:12])
                + (" ..." if len(missing) > 12 else "")
            )

    # Validate id <-> assets folder consistency for present media refs.
    if ids and asset_paths:
        asset_folders = {p.split("/")[1] for p in asset_paths if p.count("/") >= 2}
        unknown_folders = sorted(asset_folders.difference(set(ids)).difference({"brand"}))
        if unknown_folders:
            warnings.append(
                "Asset folders without matching case id: " + ", ".join(unknown_folders)
            )

    return errors, warnings


def main() -> int:
    errors, warnings = validate()

    if errors:
        print("VALIDATION_FAILED")
        for e in errors:
            print(f"- ERROR: {e}")
        for w in warnings:
            print(f"- WARN: {w}")
        return 1

    print("VALIDATION_OK")
    for w in warnings:
        print(f"- WARN: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
