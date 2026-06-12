#!/usr/bin/env python3
"""Import inbox photos into assets/ with watermark and web optimization."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from media_protect import (
    IMAGE_SUFFIXES,
    natural_sort_key,
    protect_image_file,
    iter_case_images,
)

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"


def import_inbox_folder(
    source_dir: Path,
    case_id: str,
    *,
    prefix: str,
    start_index: int,
    force: bool,
) -> list[Path]:
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source folder not found: {source_dir}")

    case_dir = ASSETS_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    sources = sorted(
        [p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES],
        key=natural_sort_key,
    )
    if not sources:
        raise RuntimeError(f"No images found in {source_dir}")

    created: list[Path] = []
    index = start_index
    for source in sources:
        ext = ".jpg" if source.suffix.lower() in {".jpg", ".jpeg", ".heic", ".heif", ".webp"} else ".png"
        target = case_dir / f"{prefix}-{index}{ext}"
        shutil.copy2(source, target)
        protect_image_file(target, force=True)
        created.append(target)
        index += 1
    return created


def protect_assets(
    *,
    case_id: str | None,
    force: bool,
) -> tuple[int, int]:
    if case_id:
        roots = [ASSETS_DIR / case_id]
    else:
        roots = [ASSETS_DIR]

    changed = 0
    skipped = 0
    for root in roots:
        for path in iter_case_images(root):
            if protect_image_file(path, force=force):
                changed += 1
                print(f"protected: {path.relative_to(ROOT)}")
            else:
                skipped += 1
    return changed, skipped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Watermark and optimize catalog images in assets/ (and import from inbox/)."
    )
    parser.add_argument("--case", help="Case id folder under assets/, e.g. na-uspenskoy")
    parser.add_argument(
        "--from",
        dest="source",
        help="Import images from inbox subfolder into assets/<case>/",
    )
    parser.add_argument(
        "--prefix",
        default="after",
        help="Filename prefix for imported images (after, before, compare, plan)",
    )
    parser.add_argument("--start", type=int, default=1, help="Starting index for imported files")
    parser.add_argument(
        "--protect-all",
        action="store_true",
        help="Watermark all case images in assets/ (skips assets/brand)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-apply watermark even if file is already protected",
    )
    args = parser.parse_args()

    if args.source:
        if not args.case:
            print("--case is required with --from", file=sys.stderr)
            return 1
        source_dir = Path(args.source)
        if not source_dir.is_absolute():
            source_dir = ROOT / source_dir
        try:
            created = import_inbox_folder(
                source_dir,
                args.case,
                prefix=args.prefix,
                start_index=args.start,
                force=True,
            )
        except (FileNotFoundError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        for path in created:
            print(f"imported: {path.relative_to(ROOT)}")
        print(f"Imported {len(created)} file(s) into assets/{args.case}/")
        return 0

    if args.protect_all or args.case:
        changed, skipped = protect_assets(case_id=args.case, force=args.force)
        print(f"Done. Protected: {changed}, skipped: {skipped}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
